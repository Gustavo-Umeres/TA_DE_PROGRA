from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import Product, Category, Cart, CartItem, Order, OrderItem, Review, User

# Registra el modelo User con el admin predeterminado de Django
admin.site.register(User, UserAdmin)

# Configuración del administrador para el modelo Product
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'price', 'stock', 'category', 'created_at')  # Incluido created_at
    search_fields = ('name', 'description')
    list_filter = ('category',)

# Configuración del administrador para el modelo Category
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name',)

# Inline para CartItem en Cart
class CartItemInline(admin.TabularInline):
    model = CartItem
    extra = 0

# Configuración del administrador para el modelo Cart
class CartAdmin(admin.ModelAdmin):
    inlines = [CartItemInline]
    list_display = ('user',)  # Muestra solo el usuario

# Inline para OrderItem en Order
class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0

# Configuración del administrador para el modelo Order
class OrderAdmin(admin.ModelAdmin):
    inlines = [OrderItemInline]
    list_display = ('user', 'total', 'created_at', 'shipping_address', 'is_paid', 'is_shipped')  # Incluido is_paid e is_shipped

# Configuración del administrador para el modelo Review
class ReviewAdmin(admin.ModelAdmin):
    list_display = ('product', 'user', 'rating', 'created_at')

# Registro de los demás modelos en el panel de administración
admin.site.register(Product, ProductAdmin)
admin.site.register(Category, CategoryAdmin)
admin.site.register(Cart, CartAdmin)
admin.site.register(Order, OrderAdmin)
admin.site.register(Review, ReviewAdmin)
