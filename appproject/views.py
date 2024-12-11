from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login, authenticate, logout
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.db.models import Min, Q
from django.utils import timezone
from django.core.paginator import Paginator
from django.http import JsonResponse
from django.conf import settings
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.core.mail import EmailMultiAlternatives
import os
from decimal import Decimal

from .forms import UserRegisterForm, UserEditForm
from .models import Product, Category, Cart, Order, OrderItem, Review, CartItem, ProductSize, ProductSizeDiscount,Filter,FilterValue

import mercadopago

User = get_user_model()


# Vista de inicio   
def home(request):
    categories = Category.objects.all()

    # Obtener productos con descuentos activos
    discounted_product_ids = ProductSizeDiscount.objects.filter(
        discount__is_active=True,
        discount__start_date__lte=timezone.now(),
        discount__end_date__gte=timezone.now()
    ).values_list('product_size__product_id', flat=True).distinct()
    
    # Filtrar los productos con los IDs obtenidos y limitarlos a 4
    products = Product.objects.filter(id__in=discounted_product_ids).distinct()[:4]
    
    # Construir datos de producto con precios mínimos, descuentos e imágenes
    product_data = []
    for product in products:
        min_price = product.sizes.aggregate(Min('price'))['price__min']
        discounted_price = None
        active_discount = ProductSizeDiscount.objects.filter(
            product_size__product=product,
            discount__is_active=True,
            discount__start_date__lte=timezone.now(),
            discount__end_date__gte=timezone.now()
        ).first()
        if active_discount:
            discounted_price = active_discount.discounted_price
        
        # Recuperar todas las imágenes del producto
        images = product.images.all()

        product_data.append({
            'product': product,
            'min_price': min_price,
            'discounted_price': discounted_price,
            'images': images  # Incluir imágenes en los datos
        })

    return render(request, 'pages/home.html', {
        'categories': categories,
        'products': product_data
    })



# Vista de registro
def register(request):
    if request.method == 'POST':
        form = UserRegisterForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.is_staff = False
            user.is_superuser = False
            user.save()
            
            raw_password = form.cleaned_data.get('password1')
            user = authenticate(username=user.username, password=raw_password)
            
            if user is not None:
                login(request, user)
                messages.success(request, 'Registro exitoso. Te has iniciado sesión automáticamente.')
                return redirect('home')
    else:
        form = UserRegisterForm()
    
    return render(request, 'registration/register.html', {'form': form})

# Vista de inicio de sesión
def login_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            messages.success(request, 'Inicio de sesión exitoso.')
            return redirect('home')
        else:
            messages.error(request, 'Credenciales incorrectas. Inténtalo de nuevo.')
    return render(request, 'registration/login.html')

# Vista de agregar producto (para administradores)
@login_required
def add_product_to_cart(request):
    if request.method == 'POST':
        product_id = request.POST.get('product_id')
        size_id = request.POST.get('size_id')
        quantity = int(request.POST.get('quantity', 1))
        
        product = get_object_or_404(Product, id=product_id)
        product_size = get_object_or_404(ProductSize, product=product, size_id=size_id)
        
        cart, created = Cart.objects.get_or_create(user=request.user)
        cart_item, created = CartItem.objects.get_or_create(cart=cart, product_size=product_size)
        
        if created:
            cart_item.quantity = quantity
        else:
            cart_item.quantity += quantity
        
        cart_item.save()
        messages.success(request, f'{quantity} unidad(es) de "{product.name}" han sido agregadas al carrito.')
        return redirect('products_list')
    return redirect('products_list')

# Vista de editar producto (para administradores)
@login_required
def edit_product(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    if request.method == 'POST':
        product.name = request.POST.get('name', product.name)
        product.description = request.POST.get('description', product.description)
        product.price = request.POST.get('price', product.price)
        product.stock = request.POST.get('stock', product.stock)
        if 'image' in request.FILES:
            product.image = request.FILES['image']
        product.save()
        messages.success(request, 'Producto editado exitosamente.')
        return redirect('products_list')
    return render(request, 'pages/edit_product.html', {'product': product})
@login_required
def add_to_cart(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    cart, created = Cart.objects.get_or_create(user=request.user)
    if request.method == 'POST':
        quantity = int(request.POST.get('quantity', 1))
        size_id = request.POST.get('size_id')
        product_size = get_object_or_404(ProductSize, product=product, size_id=size_id)

        # Verificar que la cantidad no exceda el stock disponible
        if quantity > product_size.stock:
            messages.error(request, f"No puedes agregar más de {product_size.stock} unidades de esta talla.")
            return redirect('product_detail', product_id=product_id)

        cart_item, created = CartItem.objects.get_or_create(cart=cart, product_size=product_size)
        if created:
            cart_item.quantity = quantity
        else:
            if cart_item.quantity + quantity > product_size.stock:
                messages.error(request, f"No puedes agregar más de {product_size.stock} unidades de esta talla.")
                return redirect('product_detail', product_id=product_id)
            cart_item.quantity += quantity

        cart_item.save()
        messages.success(request, f'Agregaste {quantity} unidades de "{product.name}" al carrito.')
        return redirect('products_list')
    return redirect('product_detail', product_id=product_id)


@login_required
def view_cart(request):
    # Obtener el carrito del usuario actual
    cart = get_object_or_404(Cart, user=request.user)
    cart_items = cart.items.all()

    total_price = 0

    # Calcular el precio total, considerando descuentos si están activos
    for item in cart_items:
        # Verificar si hay un descuento activo en `ProductSizeDiscount`
        discount = ProductSizeDiscount.objects.filter(
            product_size=item.product_size,
            discount__is_active=True,
            discount__start_date__lte=timezone.now(),
            discount__end_date__gte=timezone.now()
        ).first()

        # Usar el precio descontado si existe, de lo contrario, el precio regular
        if discount and discount.discounted_price:
            unit_price = discount.discounted_price
        else:
            unit_price = item.product_size.price

        # Guardar el precio unitario y el precio total por item para el template
        item.unit_price = unit_price
        item.total_price = unit_price * item.quantity
        total_price += item.total_price

    return render(request, 'pages/cart.html', {
        'cart_items': cart_items,
        'total_price': total_price,
    })


# Vista de checkout
@login_required
def checkout_view(request):
    # Obtener el carrito del usuario actual
    cart = get_object_or_404(Cart, user=request.user)
    cart_items = cart.items.all()

    total_price = 0

    # Calcular el precio total considerando descuentos cuando estén activos
    for item in cart_items:
        discount = ProductSizeDiscount.objects.filter(
            product_size=item.product_size,
            discount__is_active=True,
            discount__start_date__lte=timezone.now(),
            discount__end_date__gte=timezone.now()
        ).first()

        # Usar el precio descontado si existe, de lo contrario, el precio regular
        if discount and discount.discounted_price:
            item_price = discount.discounted_price * item.quantity
        else:
            item_price = item.product_size.price * item.quantity

        total_price += item_price

    if request.method == 'POST':
        shipping_address = request.POST.get('shipping_address')
        if not shipping_address:
            messages.error(request, 'Por favor, proporciona una dirección de envío.')
            return redirect('checkout')

        # Guardar la dirección de envío y el precio total en la sesión para el proceso de pago
        request.session['shipping_address'] = shipping_address
        request.session['total_price'] = float(total_price)  # Convertir total_price a float para la sesión
        request.session.modified = True
        return redirect('procesar_pago')

    return render(request, 'pages/checkout.html', {'cart_items': cart_items, 'total_price': total_price})

@login_required
def profile_view(request):
    if request.method == 'POST':
        form = UserEditForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Tu perfil ha sido actualizado correctamente.')
            return redirect('profile')
    else:
        form = UserEditForm(instance=request.user)
    return render(request, 'pages/profile.html', {'form': form})

# Vista de detalle del producto
def product_detail(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    reviews = product.reviews.all()

    # Obtener todas las imágenes del producto
    product_images = product.images.all()

    # Obtener los precios mínimos, descuentos y stock para cada talla del producto
    sizes_data = []
    for size in product.sizes.all():
        size_price = size.price
        stock = size.stock
        active_discount = ProductSizeDiscount.objects.filter(
            product_size=size,
            discount__is_active=True,
            discount__start_date__lte=timezone.now(),
            discount__end_date__gte=timezone.now()
        ).first()

        discounted_price = None
        if active_discount and active_discount.discounted_price:
            discounted_price = active_discount.discounted_price

        sizes_data.append({
            'size': size.size,
            'min_price': f"{size_price:.2f}",  # Formateado con 2 decimales
            'discounted_price': f"{discounted_price:.2f}" if discounted_price else None,
            'stock': stock,
        })

    # Obtener los filtros y valores de filtro aplicables al producto
    filters = Filter.objects.all()
    filter_values = {}
    for filter in filters:
        values = FilterValue.objects.filter(filter=filter)
        filter_values[filter.name] = values

    return render(request, 'pages/product_detail.html', {
        'product': product,
        'sizes_data': sizes_data,
        'reviews': reviews,
        'images': product_images,
    })


@login_required
def update_cart(request):
    cart = get_object_or_404(Cart, user=request.user)
    if request.method == 'POST':
        action = request.POST.get('action')
        
        for item in cart.items.all():
            item_id = item.id
            if f'remove_{item_id}' in action:
                item.delete()
                messages.success(request, f'El producto "{item.product_size.product.name}" ha sido eliminado del carrito.')
            elif f'decrease_{item_id}' in action and item.quantity > 1:
                item.quantity -= 1
                item.save()
                messages.success(request, f'Se ha disminuido la cantidad de "{item.product_size.product.name}".')
            elif f'increase_{item_id}' in action:
                # Verificar que la cantidad no exceda el stock disponible
                if item.quantity + 1 > item.product_size.stock:
                    messages.error(request, f'No puedes agregar más de {item.product_size.stock} unidades de esta talla.')
                else:
                    item.quantity += 1
                    item.save()
                    messages.success(request, f'Se ha aumentado la cantidad de "{item.product_size.product.name}".')
        
        return redirect('view_cart')
    return redirect('view_cart')


# Vista de agregar revisión
@login_required
def add_review(request, product_id):
    if request.method == 'POST':
        rating = request.POST.get('rating')
        comment = request.POST.get('comment')
        product = get_object_or_404(Product, id=product_id)
        
        # Verificar que se haya ingresado una calificación y un comentario
        if rating and comment:
            # Crear la revisión
            Review.objects.create(
                product=product,
                user=request.user,
                rating=rating,
                comment=comment
            )
            messages.success(request, 'Revisión agregada exitosamente.')
        else:
            messages.error(request, 'Por favor, proporciona una calificación y un comentario.')

        return redirect('product_detail', product_id=product.id)


# Vista 'Sobre Nosotros'
def about(request):
    return render(request, 'pages/about.html')

# Vista de cerrar sesión
def logout_view(request):
    logout(request)
    messages.success(request, 'Has cerrado sesión exitosamente.')
    return redirect('home')
@login_required
def procesar_pago(request):
    sdk = mercadopago.SDK(settings.MERCADOPAGO_ACCESS_TOKEN)
    shipping_address = request.session.get('shipping_address')
    total_price = request.session.get('total_price')

    if not shipping_address or total_price is None:
        messages.error(request, 'Hubo un problema con los datos de envío o el total a pagar.')
        return redirect('checkout')

    # Obtener el carrito del usuario actual
    cart = get_object_or_404(Cart, user=request.user)
    cart_items = cart.items.all()

    # Crear lista de ítems con precios considerando los descuentos
    items = []
    for item in cart_items:
        # Verificar si hay un descuento activo
        discount = ProductSizeDiscount.objects.filter(
            product_size=item.product_size,
            discount__is_active=True,
            discount__start_date__lte=timezone.now(),
            discount__end_date__gte=timezone.now()
        ).first()

        # Usar el precio con descuento si existe, de lo contrario el precio regular
        if discount and discount.discounted_price:
            unit_price = float(discount.discounted_price)
        else:
            unit_price = float(item.product_size.price)

        # Crear el item para Mercado Pago
        items.append({
            "title": item.product_size.product.name,
            "quantity": item.quantity,
            "unit_price": unit_price,
            "currency_id": "PEN"
        })

    # Configurar los datos de la preferencia para Mercado Pago
    preference_data = {
        "items": items,
        "payer": {"email": request.user.email},
        "back_urls": {
            "success": f"{os.getenv('DOMAIN')}/pagos/exito/",
            "failure": f"{os.getenv('DOMAIN')}/pagos/fallo/",
            "pending": f"{os.getenv('DOMAIN')}/pagos/pendiente/",
        },
        "auto_return": "approved",
        "shipment": {"receiver_address": {"street_name": shipping_address}}
    }

    # Crear preferencia de pago en Mercado Pago
    preference_response = sdk.preference().create(preference_data)
    preference = preference_response["response"]
    return redirect(preference['init_point'])
@login_required
def pago_exito(request):
    try:
        # Obtener datos de la sesión
        shipping_address = request.session.get('shipping_address')
        total_price = request.session.get('total_price')

        if not shipping_address or total_price is None:
            messages.error(request, 'Hubo un problema con los datos de envío o el total a pagar.')
            return redirect('checkout')

        # Obtener el carrito del usuario actual
        cart = get_object_or_404(Cart, user=request.user)

        # Crear la orden
        order = Order.objects.create(
            user=request.user,
            shipping_address=shipping_address,
            total=total_price,
            is_paid=True
        )

        # Crear elementos de la orden y actualizar stock
        for item in cart.items.all():
            # Verificar si hay un descuento activo para este product_size
            discount = ProductSizeDiscount.objects.filter(
                product_size=item.product_size,
                discount__is_active=True,
                discount__start_date__lte=timezone.now(),
                discount__end_date__gte=timezone.now()
            ).first()

            # Usar el precio con descuento si existe, de lo contrario, el precio regular
            if discount and discount.discounted_price:
                item_price = discount.discounted_price
            else:
                item_price = item.product_size.price

            # Crear el OrderItem con el precio correcto
            OrderItem.objects.create(
                order=order,
                product_size=item.product_size,
                quantity=item.quantity,
                price=item_price * item.quantity  # Guardar el subtotal del producto con la cantidad
            )

            # Reducir el stock del producto
            item.product_size.stock -= item.quantity
            item.product_size.save()

        # Limpiar el carrito después de procesar la orden
        cart.items.all().delete()

        # Enviar correo de confirmación de pedido
        send_order_confirmation_email(request, order)

        # Limpiar datos de la sesión
        del request.session['shipping_address']
        del request.session['total_price']
        request.session.modified = True

        messages.success(request, 'El pago fue exitoso y tu pedido ha sido creado.')
        return redirect('home')

    except Exception as e:
        print(f"Error en pago_exito: {e}")
        messages.error(request, 'Ocurrió un error inesperado. Intenta de nuevo o contacta soporte.')
        return redirect('checkout')


def send_order_confirmation_email(request, order):
    try:
        # Obtener los elementos de la orden y asegurar que `size` esté disponible
        order_items = order.items.select_related('product_size__size').all()
        
        subject = "Confirmación de tu compra en GOTTA"
        html_message = render_to_string('emails/confirmacion_compra.html', {
            'user': request.user,
            'order': order,
            'items': order_items,
            'total_price': order.total,
            'shipping_address': order.shipping_address,
        })
        plain_message = strip_tags(html_message)
        
        email = EmailMultiAlternatives(
            subject,
            plain_message,
            settings.DEFAULT_FROM_EMAIL,
            [request.user.email]
        )
        email.attach_alternative(html_message, "text/html")
        email.send()

    except Exception as e:
        print(f"Error al enviar el correo de confirmación: {e}")
        messages.error(request, 'No se pudo enviar la confirmación del pedido por correo.')



@login_required
def pago_fallo(request):
    messages.error(request, 'El pago falló. Intenta nuevamente.')
    return redirect('checkout')

@login_required
def pago_pendiente(request):
    messages.warning(request, 'El pago está pendiente. Te notificaremos cuando se complete.')
    return redirect('home')


def products_list(request):
    query = request.GET.get('q', '')
    category_id = request.GET.get('category', 'all')
    selected_filters = request.GET.getlist('filter')  # Obtener múltiples filtros
    categories = Category.objects.all()

    # Obtener filtros y organizar los valores de filtro por categorías relevantes
    filters = Filter.objects.all()
    attribute_filters = {filter.name: filter.values.all() for filter in filters}  # Agrupa valores por filtro

    # Filtrar productos
    products = Product.objects.all().order_by('id')
    if query:
        products = products.filter(Q(name__icontains=query) | Q(description__icontains=query))
    if category_id != 'all':
        products = products.filter(category_id=category_id)
    if selected_filters:
        products = products.filter(filter_values__filter_value__id__in=selected_filters).distinct()

    # Construir datos de producto con precios mínimos, descuentos e imágenes
    product_data = []
    for product in products:
        min_price = product.sizes.aggregate(Min('price'))['price__min']
        discounted_price = None
        active_discount = product.sizes.filter(discounts__discount__is_active=True).first()
        if active_discount:
            discounted_price = active_discount.discounts.first().discounted_price
        
        # Obtener la primera imagen del producto
        first_image = product.images.first()

        product_data.append({
            'product': product,
            'min_price': min_price,
            'discounted_price': discounted_price,
            'first_image': first_image  # Incluir la primera imagen
        })

    # Paginación
    paginator = Paginator(product_data, 15)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'pages/products_list.html', {
        'categories': categories,
        'attribute_filters': attribute_filters,  # Pasar los filtros organizados
        'page_obj': page_obj,
        'selected_category': category_id,
        'selected_filters': selected_filters,  # Pasar todos los filtros seleccionados
    })
    
    
    
def search_products(request):
    query = request.GET.get('q', '')
    products = Product.objects.filter(Q(name__icontains=query) | Q(description__icontains=query)).order_by('name')
    
    products_list = []
    for product in products:
        # Obtener el precio mínimo de las tallas del producto
        min_price = product.sizes.aggregate(Min('price'))['price__min']
        discounted_price = None
        
        # Verificar si hay un descuento activo en alguna talla
        active_discount = ProductSizeDiscount.objects.filter(
            product_size__product=product,
            discount__is_active=True,
            discount__start_date__lte=timezone.now(),
            discount__end_date__gte=timezone.now()
        ).first()
        
        if active_discount:
            discounted_price = active_discount.discounted_price
        
        # Obtener la primera imagen del producto para mostrar en los resultados
        first_image = product.images.first().image.url if product.images.exists() else None

        # Agregar información del producto a la lista de resultados
        products_list.append({
            'id': product.id,
            'name': product.name,
            'price': min_price,
            'discounted_price': discounted_price,
            'image': first_image
        })

    return JsonResponse({'products': products_list})



def products_by_category(request, category_id):
    category = get_object_or_404(Category, id=category_id)
    products = Product.objects.filter(category=category).order_by('id')
    
    # Construir datos de producto con precios mínimos, descuentos e imágenes
    product_data = []
    for product in products:
        min_price = product.sizes.aggregate(Min('price'))['price__min']
        discounted_price = None
        
        # Verificar si hay un descuento activo en alguna talla
        active_discount = ProductSizeDiscount.objects.filter(
            product_size__product=product,
            discount__is_active=True,
            discount__start_date__lte=timezone.now(),
            discount__end_date__gte=timezone.now()
        ).first()
        
        if active_discount:
            discounted_price = active_discount.discounted_price
        
        # Obtener la primera imagen del producto
        first_image = product.images.first().image.url if product.images.exists() else None

        # Agregar información del producto a la lista de productos
        product_data.append({
            'product': product,
            'min_price': min_price,
            'discounted_price': discounted_price,
            'first_image': first_image  # Incluir la primera imagen
        })

    # Paginación
    paginator = Paginator(product_data, 12)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'pages/products_list.html', {
        'category': category,
        'page_obj': page_obj,
        'products': product_data,
    })


from decimal import Decimal
def product_list_view(request):
    # Obtener todos los productos con al menos una talla que tenga precio
    products = Product.objects.filter(sizes__price__isnull=False).distinct().order_by('id')

    # Construir datos de producto con precios mínimos, descuentos e imágenes
    product_data = []
    for product in products:
        min_price = get_min_price_and_discount(product)  # Usa la función utilitaria
        first_image = product.images.first().image.url if product.images.exists() else None

        product_data.append({
            'product': product,
            'min_price': min_price,
            'first_image': first_image,  # Incluir la primera imagen
        })

    # Paginación
    paginator = Paginator(product_data, 10)  # Muestra 10 productos por página
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'pages/products_list.html', {
        'page_obj': page_obj,
        'categories': Category.objects.all(),
    })
    
def get_min_price_and_discount(product):
    min_price = Decimal('Infinity')  # Inicializa con un valor muy alto
    discounted_price = None

    for size in product.sizes.all():
        size_price = size.price
        active_discount = ProductSizeDiscount.objects.filter(
            product_size=size,
            discount__is_active=True,
            discount__start_date__lte=timezone.now(),
            discount__end_date__gte=timezone.now()
        ).first()

        # Si hay descuento, considera el precio con descuento
        if active_discount and active_discount.discounted_price is not None:
            size_price = min(size_price, active_discount.discounted_price)

        # Actualizar el precio mínimo global
        if size_price < min_price:
            min_price = size_price

    return round(min_price, 2) if min_price != Decimal('Infinity') else None
