from django.db import models
from django.contrib.auth.models import AbstractUser

# Modelo de Usuario
class User(AbstractUser):
    # Puedes añadir campos adicionales que necesites aquí
    is_admin = models.BooleanField(default=False)  # Ejemplo de campo adicional

    # Añade 'related_name' para evitar conflictos
    groups = models.ManyToManyField(
        'auth.Group',
        related_name='appproject_user_groups',  # Cambiado aquí para evitar conflictos
        blank=True,
        help_text='Los grupos a los que pertenece este usuario.',
        verbose_name='grupos'
    )
    user_permissions = models.ManyToManyField(
        'auth.Permission',
        related_name='appproject_user_permissions',  # Cambiado aquí para evitar conflictos
        blank=True,
        help_text='Permisos específicos para este usuario.',
        verbose_name='permisos de usuario'
    )

    def __str__(self):
        return self.username

# Modelo de Categoría
class Category(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)

    def __str__(self):
        return self.name

# Modelo de Producto
class Product(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    stock = models.PositiveIntegerField()
    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    image = models.ImageField(upload_to='products/')
    created_at = models.DateTimeField(auto_now_add=True)  # Este campo debe estar presente

    def __str__(self):
        return self.name

# Modelo de Pedido
class Order(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    total = models.DecimalField(max_digits=10, decimal_places=2)
    is_paid = models.BooleanField(default=False)
    is_shipped = models.BooleanField(default=False)  # Para indicar si el pedido ha sido enviado
    shipping_address = models.TextField()  # Dirección de envío

    def __str__(self):
        return f'Pedido {self.id} por {self.user.username}'

# Modelo de Ítem de Pedido
class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField()
    price = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f'{self.quantity} de {self.product.name} en el pedido {self.order.id}'

# Modelo de Carrito
class Cart(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'Carrito para {self.user.username}'

# Modelo de Ítem de Carrito
class CartItem(models.Model):
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField()

    def __str__(self):
        return f'{self.quantity} de {self.product.name} en el carrito'

# Modelo de Revisión
class Review(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='reviews')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    rating = models.PositiveIntegerField()  # Calificación entre 1 y 5
    comment = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'Revisión para {self.product.name} por {self.user.username}'
