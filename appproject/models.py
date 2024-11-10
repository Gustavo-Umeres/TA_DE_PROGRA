from django.db import models
from django.contrib.auth.models import AbstractUser
from cloudinary_storage.storage import MediaCloudinaryStorage

# Modelo de Usuario
class User(AbstractUser):
    def __str__(self):
        return self.username

# Modelo de Categoría
class Category(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)

    def __str__(self):
        return self.name

# Modelo de Talla
class Size(models.Model):
    name = models.CharField(max_length=10, unique=True)

    def __str__(self):
        return self.name

# Modelo de Producto
class Product(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField()
    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    image = models.ImageField(storage=MediaCloudinaryStorage(), upload_to='products/')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

# Modelo de Relación entre Producto y Talla (con Precio Específico)
class ProductSize(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='sizes')
    size = models.ForeignKey(Size, on_delete=models.CASCADE)
    price = models.DecimalField(max_digits=10, decimal_places=2)  # Precio específico por talla
    stock = models.PositiveIntegerField(default=0)

    def __str__(self):
        return f'{self.product.name} - Talla: {self.size.name}'

# Modelo de Descuento
class Discount(models.Model):
    name = models.CharField(max_length=100)
    discount_type = models.CharField(max_length=10, choices=[('fixed', 'Fixed'), ('percentage', 'Percentage')])
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    start_date = models.DateTimeField()
    end_date = models.DateTimeField()
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f'{self.name} ({self.discount_type})'

# Relación entre ProductSize y Descuento (con Precio Descontado)
class ProductSizeDiscount(models.Model):
    product_size = models.ForeignKey(ProductSize, on_delete=models.CASCADE, related_name='discounts')
    discount = models.ForeignKey(Discount, on_delete=models.CASCADE)
    discounted_price = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)

    def __str__(self):
        return f'{self.discount.name} aplicado a {self.product_size.product.name} - Talla: {self.product_size.size.name}'

    def save(self, *args, **kwargs):
        # Calcula el precio con descuento
        if self.product_size and self.discount:
            original_price = self.product_size.price
            if self.discount.discount_type == 'fixed':
                self.discounted_price = max(original_price - self.discount.amount, 0)
            elif self.discount.discount_type == 'percentage':
                self.discounted_price = max(original_price * (1 - self.discount.amount / 100), 0)
        super().save(*args, **kwargs)

# Modelo de Pedido
class Order(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    total = models.DecimalField(max_digits=10, decimal_places=2)
    is_paid = models.BooleanField(default=False)
    is_shipped = models.BooleanField(default=False)
    shipping_address = models.TextField()

    def __str__(self):
        return f'Pedido {self.id} por {self.user.username}'

# Modelo de Ítem de Pedido
class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    product_size = models.ForeignKey(ProductSize, on_delete=models.CASCADE)  # Relación con talla específica
    quantity = models.PositiveIntegerField()
    price = models.DecimalField(max_digits=10, decimal_places=2)  # Precio al momento de la compra

    def __str__(self):
        return f'{self.quantity} de {self.product_size.product.name} (Talla: {self.product_size.size.name}) en el pedido {self.order.id}'

# Modelo de Carrito
class Cart(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'Carrito para {self.user.username}'

# Modelo de Ítem de Carrito
class CartItem(models.Model):
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name='items')
    product_size = models.ForeignKey(ProductSize, on_delete=models.CASCADE)  # Relación con talla específica
    quantity = models.PositiveIntegerField(default=1)

    def __str__(self):
        return f'{self.quantity} de {self.product_size.product.name} (Talla: {self.product_size.size.name}) en el carrito'

    def save(self, *args, **kwargs):
        if self.quantity < 1:
            self.quantity = 1  # Asegurar cantidad mínima de 1
        super().save(*args, **kwargs)

# Modelo de Revisión
class Review(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='reviews')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    rating = models.PositiveIntegerField()  # Calificación de 1 a 5
    comment = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'Revisión para {self.product.name} por {self.user.username}'

# Modelo de Filtros
class Filter(models.Model):
    name = models.CharField(max_length=50)  # Ej.: Edad, Color, Material, Género
    description = models.TextField(blank=True)

    def __str__(self):
        return self.name

# Relación entre Producto y Filtro
class ProductFilter(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='filters')
    filter = models.ForeignKey(Filter, on_delete=models.CASCADE, related_name='products')

    def __str__(self):
        return f'{self.product.name} - {self.filter.name}'