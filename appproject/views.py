from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login, authenticate, logout
from django.contrib import messages
from django.contrib.auth import get_user_model  # Usar get_user_model para obtener el modelo de usuario personalizado
from .forms import UserRegisterForm
from .models import Product, Category, Cart, Order, OrderItem, Review, CartItem

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
            login(request, user)
            messages.success(request, 'Registro exitoso.')
            return redirect('home')
    else:
        form = UserRegisterForm()
    return render(request, 'registration/register.html', {'form': form})


# Vista de inicio de sesión
def login_view(request):
    print("Cookies:", request.COOKIES)  # Mensaje de depuración
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        print(f"Intentando iniciar sesión con: {username}")
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
def add_product(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        description = request.POST.get('description')
        price = request.POST.get('price')
        stock = request.POST.get('stock')
        category_id = request.POST.get('category')
        image = request.FILES.get('image')

        if all([name, description, price, stock, category_id, image]):  # Verificar que todos los campos estén presentes
            category = get_object_or_404(Category, id=category_id)
            product = Product(
                name=name,
                description=description,
                price=price,
                stock=stock,
                category=category,
                image=image
            )
            product.save()
            messages.success(request, 'Producto agregado exitosamente.')
            return redirect('products_list')

    categories = Category.objects.all()
    return render(request, 'pages/add_product.html', {'categories': categories})

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
        # Asegúrate de que 'quantity' viene en el POST request y convierte a entero.
        try:
            quantity = int(request.POST.get('quantity', 1))  # Por defecto 1 si no se especifica cantidad.
        except (TypeError, ValueError):
            messages.error(request, 'Cantidad no válida.')
            return redirect('product_detail', product_id=product_id)

        if quantity <= 0:
            messages.error(request, 'La cantidad debe ser mayor que cero.')
            return redirect('product_detail', product_id=product_id)

        # Verifica si el ítem ya está en el carrito
        cart_item, created = CartItem.objects.get_or_create(cart=cart, product=product)

        if created:
            # Si es un nuevo ítem, asigna la cantidad seleccionada
            cart_item.quantity = quantity
        else:
            # Si el ítem ya existe, actualiza la cantidad
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
        item.total_price = item.product.price * item.quantity  # Calcula el total por ítem
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
        item.total_price = item.product.price * item.quantity  # Calcula el total por ítem
        total_price += item.total_price  # Suma al precio total del carrito

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
                OrderItem.objects.create(
                    order=order,
                    product=item.product,
                    quantity=item.quantity,
                    price=item.product.price
                )

            # Limpiar el carrito
            cart_items.delete()

            messages.success(request, 'Tu pedido ha sido realizado con éxito.')
            return redirect('home')  # Redirigir a la página de inicio o una página de confirmación

    return render(request, 'pages/checkout.html', {
        'cart_items': cart_items,
        'total_price': total_price
    })


# Vista de producto individual
def product_detail(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    reviews = product.reviews.all()  # Obtener las revisiones del producto
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
