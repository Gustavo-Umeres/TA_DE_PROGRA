from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login, authenticate, logout
from django.contrib import messages
from django.contrib.auth import get_user_model  # Usar get_user_model para obtener el modelo de usuario personalizado
from .forms import UserRegisterForm
from .models import Product, Category, Cart, Order, OrderItem, Review, CartItem, ProductSize

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
        # Acceder al producto a través de 'product_size'
        item_total_price = item.product_size.product.price * item.quantity  # Calcula el total por ítem
        item.total_price = item_total_price
        total_price += item_total_price  # Suma al precio total del carrito

    if request.method == 'POST':
        # Obtener la dirección de envío del formulario
        shipping_address = request.POST.get('shipping_address')
        if shipping_address:
            # Crear el pedido
            order = Order.objects.create(
                user=request.user,
                shipping_address=shipping_address,
                total=total_price,
                is_paid=False  # Esto puede cambiar cuando se implemente el pago real
            )

            # Crear los ítems del pedido basados en los ítems del carrito
            for item in cart_items:
                # Aquí guardamos el precio total (precio por cantidad)
                OrderItem.objects.create(
                    order=order,
                    product_size=item.product_size,
                    quantity=item.quantity,
                    price=item.total_price  # Guardar el precio total (precio unitario * cantidad)
                )

            # Limpiar el carrito
            cart_items.delete()

            messages.success(request, 'Tu pedido ha sido realizado con éxito.')
            return redirect('home')  # Redirigir a la página de inicio o una página de confirmación

    return render(request, 'pages/checkout.html', {
        'cart_items': cart_items,
        'total_price': total_price
    })



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
