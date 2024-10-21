from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login, authenticate, logout
from django.contrib import messages
from django.contrib.auth import get_user_model
from .forms import UserRegisterForm
from .models import Product, Category, Cart, Order, OrderItem, Review, CartItem, ProductSize
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.contrib import messages
from .forms import UserEditForm
import mercadopago
from django.conf import settings
from django.core.paginator import Paginator
from django.db.models import Q
from django.http import JsonResponse

User = get_user_model()  # Usar el modelo de usuario correcto

# Vista de inicio
def home(request):
    categories = Category.objects.all()
    products = Product.objects.all()  # Mostrar todos los productos
    return render(request, 'pages/home.html', {'categories': categories, 'products': products})

# Vista de lista de productos
def products_list(request):
    products = Product.objects.all()  # Mostrar todos los productos
    return render(request, 'pages/products_list.html', {'products': products})

# Vista de registro
def register(request):
    if request.method == 'POST':
        form = UserRegisterForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.is_staff = False  # No debe ser parte del staff
            user.is_superuser = False  # No debe ser superusuario
            user.save()
            
            # Autenticar al usuario antes de iniciar sesión
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
        # Obteniendo los datos del producto desde la solicitud POST
        product_id = request.POST.get('product_id')
        size_id = request.POST.get('size_id')
        quantity = int(request.POST.get('quantity', 1))  # La cantidad que se desea agregar
        
        # Validación del producto y talla
        product = get_object_or_404(Product, id=product_id)
        product_size = get_object_or_404(ProductSize, product=product, size_id=size_id)
        
        # Obtenemos o creamos el carrito del usuario
        cart, created = Cart.objects.get_or_create(user=request.user)
        
        # Verificamos si el item ya está en el carrito
        cart_item, created = CartItem.objects.get_or_create(cart=cart, product_size=product_size)
        
        if created:
            cart_item.quantity = quantity
        else:
            cart_item.quantity += quantity
        
        cart_item.save()

        messages.success(request, f'{quantity} unidad(es) de "{product.name}" han sido agregadas al carrito.')
        return redirect('products_list')  # Redirigir a la lista de productos o donde prefieras

    return redirect('products_list')  # Redirigir si no es una solicitud POST



@login_required
def add_to_cart(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    cart, created = Cart.objects.get_or_create(user=request.user)

    if request.method == 'POST':
        try:
            quantity = int(request.POST.get('quantity', 1))
        except (TypeError, ValueError):
            messages.error(request, 'Cantidad no válida.')
            return redirect('product_detail', product_id=product_id)

        if quantity <= 0:
            messages.error(request, 'La cantidad debe ser mayor que cero.')
            return redirect('product_detail', product_id=product_id)

        # Obtener el size_id desde el formulario
        size_id = request.POST.get('size_id')
        if not size_id:
            messages.error(request, 'Por favor selecciona una talla.')
            return redirect('product_detail', product_id=product_id)

        # Verificar que el tamaño del producto existe
        product_size = get_object_or_404(ProductSize, product=product, size_id=size_id)

        # Verificar si el ítem ya está en el carrito
        cart_item, created = CartItem.objects.get_or_create(cart=cart, product_size=product_size)

        if created:
            cart_item.quantity = quantity
        else:
            cart_item.quantity += quantity

        cart_item.save()
        messages.success(request, f'Agregaste {quantity} unidades de "{product.name}" al carrito.')
        return redirect('products_list')

    return redirect('product_detail', product_id=product_id)

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
        try:
            quantity = int(request.POST.get('quantity', 1))
        except (TypeError, ValueError):
            messages.error(request, 'Cantidad no válida.')
            return redirect('product_detail', product_id=product_id)

        if quantity <= 0:
            messages.error(request, 'La cantidad debe ser mayor que cero.')
            return redirect('product_detail', product_id=product_id)

        # Aquí debes obtener el tamaño correspondiente de la forma que necesites
        size_id = request.POST.get('size_id')  # Asegúrate de que estás obteniendo el ID de la talla
        product_size = get_object_or_404(ProductSize, product=product, size_id=size_id)

        # Verifica si el ítem ya está en el carrito
        cart_item, created = CartItem.objects.get_or_create(cart=cart, product_size=product_size)

        if created:
            cart_item.quantity = quantity
        else:
            cart_item.quantity += quantity

        cart_item.save()
        messages.success(request, f'Agregaste {quantity} unidades de "{product.name}" al carrito.')
        return redirect('products_list')

    return redirect('product_detail', product_id=product_id)


@login_required
def view_cart(request):
    cart = get_object_or_404(Cart, user=request.user)
    cart_items = cart.items.all()

    total_price = 0
    for item in cart_items:
        # Acceder al producto a través de 'product_size'
        item.total_price = item.product_size.product.price * item.quantity  # Calcula el total por ítem
        total_price += item.total_price  # Suma al precio total del carrito

    return render(request, 'pages/cart.html', {
        'cart_items': cart_items,
        'total_price': total_price
    })


# Vista de checkout
@login_required
def checkout_view(request):
    cart = get_object_or_404(Cart, user=request.user)
    cart_items = cart.items.all()

    total_price = 0
    for item in cart_items:
        item_total_price = float(item.product_size.product.price * item.quantity)  # Asegúrate de convertir a float
        total_price += item_total_price

    if request.method == 'POST':
        # Obtener dirección de envío del formulario
        shipping_address = request.POST.get('shipping_address')

        # Verificar que la dirección esté presente
        if not shipping_address:
            messages.error(request, 'Por favor, proporciona una dirección de envío.')
            return redirect('checkout')

        # Guardar en la sesión, convertir total_price a float
        request.session['shipping_address'] = shipping_address
        request.session['total_price'] = float(total_price)  # Convertir el total a float
        request.session.modified = True  # Asegúrate de que la sesión se actualice

        # Redirigir al usuario a la vista de procesar pago
        return redirect('procesar_pago')

    return render(request, 'pages/checkout.html', {
        'cart_items': cart_items,
        'total_price': total_price
    })

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
    reviews = product.reviews.all()  # Obtener todas las reseñas del producto

    if request.method == 'POST' and request.user.is_authenticated:
        rating = request.POST.get('rating')
        comment = request.POST.get('comment')
        
        if rating and comment:  # Asegúrate de que ambos campos estén presentes
            Review.objects.create(product=product, user=request.user, rating=rating, comment=comment)
            messages.success(request, 'Revisión agregada exitosamente.')
            return redirect('product_detail', product_id=product.id)
        else:
            messages.error(request, 'Por favor, llena todos los campos.')

    return render(request, 'pages/product_detail.html', {'product': product, 'reviews': reviews})

@login_required
def update_cart(request):
    cart = get_object_or_404(Cart, user=request.user)
    if request.method == 'POST':
        action = request.POST.get('action')

        for item in cart.items.all():
            item_id = item.id

            if f'remove_{item_id}' in action:
                item.delete()  # Elimina el ítem del carrito
                messages.success(request, f'El producto "{item.product_size.product.name}" ha sido eliminado del carrito.')
            
            elif f'decrease_{item_id}' in action and item.quantity > 1:
                item.quantity -= 1  # Disminuye la cantidad
                item.save()
                messages.success(request, f'Se ha disminuido la cantidad de "{item.product_size.product.name}".')
            
            elif f'increase_{item_id}' in action:
                item.quantity += 1  # Aumenta la cantidad
                item.save()
                messages.success(request, f'Se ha aumentado la cantidad de "{item.product_size.product.name}".')

        return redirect('view_cart')  # Redirige nuevamente al carrito

    return redirect('view_cart')


# Vista de agregar revisión
@login_required
def add_review(request, product_id):
    if request.method == 'POST':
        rating = request.POST.get('rating')
        comment = request.POST.get('comment')
        product = get_object_or_404(Product, id=product_id)
        if rating and comment:  # Asegúrate de que ambos campos estén presentes
            Review.objects.create(product=product, user=request.user, rating=rating, comment=comment)
            messages.success(request, 'Revisión agregada exitosamente.')
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

    # Depuración para verificar los valores de la sesión
    shipping_address = request.session.get('shipping_address')
    total_price = request.session.get('total_price')

    # Verificar que los datos existan
    if not shipping_address or not total_price:
        messages.error(request, 'Hubo un problema con los datos de envío o el total a pagar.')
        return redirect('checkout')

    cart = get_object_or_404(Cart, user=request.user)
    cart_items = cart.items.all()

    items = []
    for item in cart_items:
        product_name = item.product_size.product.name
        product_price = float(item.product_size.product.price)
        quantity = item.quantity

        items.append({
            "title": product_name,
            "quantity": quantity,
            "unit_price": product_price,
            "currency_id": "PEN"  # O la moneda que utilices
        })

    # Crear la preferencia de pago
    preference_data = {
        "items": items,
        "payer": {
            "email": request.user.email,
        },
        "back_urls": {
            "success": "http://localhost:8000/pagos/exito/",
            "failure": "http://localhost:8000/pagos/fallo/",
            "pending": "http://localhost:8000/pagos/pendiente/",
        },
        "auto_return": "approved",
        "shipment": {
            "receiver_address": {
                "street_name": shipping_address,  # Dirección de envío
            }
        }
    }

    preference_response = sdk.preference().create(preference_data)
    preference = preference_response["response"]

    # Redirigir al usuario al sandbox de Mercado Pago
    return redirect(preference['init_point'])


@login_required
def pago_exito(request):
    # Verificar que los datos de la sesión existan
    shipping_address = request.session.get('shipping_address')
    total_price = request.session.get('total_price')

    # Imprimir valores de la sesión para depuración
    print(f"Shipping Address: {shipping_address}, Total Price: {total_price}")

    if not shipping_address or not total_price:
        messages.error(request, 'Hubo un problema con el pago. Intenta nuevamente.')
        return redirect('checkout')

    # Crear el pedido
    cart = get_object_or_404(Cart, user=request.user)
    cart_items = cart.items.all()

    order = Order.objects.create(
        user=request.user,
        shipping_address=shipping_address,
        total=total_price,
        is_paid=True
    )

    # Crear los ítems del pedido basados en el carrito
    for item in cart_items:
        OrderItem.objects.create(
            order=order,
            product_size=item.product_size,
            quantity=item.quantity,
            price=item.product_size.product.price * item.quantity
        )

    # Limpiar el carrito
    cart_items.delete()

    messages.success(request, 'El pago fue exitoso y tu pedido ha sido creado.')
    return redirect('home')

@login_required
def pago_fallo(request):
    messages.error(request, 'El pago falló. Intenta nuevamente.')
    return redirect('checkout')

@login_required
def pago_pendiente(request):
    messages.warning(request, 'El pago está pendiente. Te notificaremos cuando se complete.')
    return redirect('home')


def products_list(request):
    product_list = Product.objects.all().order_by('name')  # Agregar un campo para ordenar
    paginator = Paginator(product_list, 12)  # Muestra 12 productos por página
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    return render(request, 'pages/products_list.html', {'page_obj': page_obj})


def products_list(request):
    query = request.GET.get('q')  # Para la búsqueda
    category_id = request.GET.get('category')  # Capturar el filtro de categoría

    # Obtener todas las categorías
    categories = Category.objects.all()

    # Filtrar productos por búsqueda y/o categoría
    products = Product.objects.all()
    
    if query:
        products = products.filter(name__icontains=query)

    if category_id:
        category = get_object_or_404(Category, id=category_id)
        products = products.filter(category=category)

    # Paginación de los productos
    paginator = Paginator(products, 12)  # 12 productos por página
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'pages/products_list.html', {
        'categories': categories,
        'page_obj': page_obj,
        'selected_category': category_id
    })
def search_products(request):
    query = request.GET.get('q', '')  # Obtener el término de búsqueda
    products = Product.objects.filter(Q(name__icontains=query) | Q(description__icontains=query)).order_by('name')

    # Serializar los productos
    products_list = [
        {
            'id': product.id,
            'name': product.name,
            'price': str(product.price),  # Convertir el precio a string para el JSON
            'image': product.image.url,
        }
        for product in products
    ]

    return JsonResponse({'products': products_list})


def products_by_category(request, category_id):
    # Obtener la categoría o devolver un error 404 si no existe
    category = get_object_or_404(Category, id=category_id)
    
    # Filtrar productos por la categoría seleccionada
    products = Product.objects.filter(category=category)
    
    # Paginación
    paginator = Paginator(products, 12)  # Muestra 12 productos por página
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Renderizar la página de productos filtrados por categoría
    return render(request, 'pages/products_list.html', {
        'category': category,
        'page_obj': page_obj,  # Paginación de productos
        'products': products  # Productos filtrados
    })
