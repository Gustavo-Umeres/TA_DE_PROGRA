from django.db import models
from django.contrib.auth.models import AbstractUser
from cloudinary_storage.storage import MediaCloudinaryStorage

# Modelo de Usuario
class User(AbstractUser):
    # Puedes añadir campos adicionales que necesites aquí
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

# Modelo de Producto
class Product(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    image = models.ImageField(storage=MediaCloudinaryStorage(), upload_to='products/')  # Usar almacenamiento de Cloudinary
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

# Modelo de Relación entre Producto y Talla
class ProductSize(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='sizes')
    size = models.ForeignKey(Size, on_delete=models.CASCADE)
    stock = models.PositiveIntegerField(default=0)

    def __str__(self):
        return f'{self.product.name} - Talla: {self.size.name}'

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
    product_size = models.ForeignKey(ProductSize, on_delete=models.CASCADE)  # Relación con tamaño específico
    quantity = models.PositiveIntegerField()
    price = models.DecimalField(max_digits=10, decimal_places=2)

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
    product_size = models.ForeignKey(ProductSize, on_delete=models.CASCADE)  # Relación con tamaño específico
    quantity = models.PositiveIntegerField(default=1)  # Añadimos valor por defecto

    def __str__(self):
        return f'{self.quantity} de {self.product_size.product.name} (Talla: {self.product_size.size.name}) en el carrito'

    def save(self, *args, **kwargs):
        if self.quantity < 1:
            self.quantity = 1  # Asegurarse de que la cantidad mínima sea 1
        super().save(*args, **kwargs)

# Modelo de Revisión
class Review(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='reviews')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    rating = models.PositiveIntegerField()  # Calificación entre 1 y 5
    comment = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'Revisión para {self.product.name} por {self.user.username}'
