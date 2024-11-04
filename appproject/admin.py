from django.contrib import admin
from .models import User, Category, Size, Product, ProductSize, Order, OrderItem, Cart, CartItem, Review
from django.db.models import Sum

# Inline para OrderItem
class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0

# Inline para CartItem
class CartItemInline(admin.TabularInline):
    model = CartItem
    extra = 0

@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ('username', 'email', 'is_staff', 'is_active')
    search_fields = ('username', 'email')

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'description')
    search_fields = ('name',)

@admin.register(Size)
class SizeAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'price', 'total_stock', 'category', 'created_at')
    list_filter = ('category',)
    search_fields = ('name', 'description')

    def total_stock(self, obj):
        # Calcula el stock total sumando el stock de todas las tallas
        return ProductSize.objects.filter(product=obj).aggregate(total=Sum('stock'))['total'] or 0
    total_stock.short_description = 'Total Stock'

@admin.register(ProductSize)
class ProductSizeAdmin(admin.ModelAdmin):
    list_display = ('product', 'size', 'stock')
    search_fields = ('product__name', 'size__name')

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'total', 'is_paid', 'is_shipped', 'created_at')
    list_filter = ('is_paid', 'is_shipped')
    search_fields = ('user__username',)
    readonly_fields = ('total', 'created_at', 'updated_at')
    inlines = [OrderItemInline]  # Referenciando la clase inline correctamente

@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ('order', 'product_size', 'quantity', 'price')
    search_fields = ('order__id', 'product_size__product__name')

@admin.register(Cart)
class CartAdmin(admin.ModelAdmin):
    list_display = ('user', 'created_at')
    search_fields = ('user__username',)
    inlines = [CartItemInline]  # Referenciando la clase inline correctamente

@admin.register(CartItem)
class CartItemAdmin(admin.ModelAdmin):
    list_display = ('cart', 'product_size', 'quantity')
    search_fields = ('cart__user__username', 'product_size__product__name')

@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ('product', 'user', 'rating', 'created_at')
    list_filter = ('rating',)
    search_fields = ('product__name', 'user__username')
