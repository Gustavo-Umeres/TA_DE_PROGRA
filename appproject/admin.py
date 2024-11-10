from django.contrib import admin
from .models import (
    User, Category, Size, Product, ProductSize, Order, OrderItem,
    Cart, CartItem, Review, Discount, ProductSizeDiscount,
    Filter, ProductFilter
)
from django.db.models import Sum

# Inline for OrderItem
class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ('price',)

# Inline for CartItem
class CartItemInline(admin.TabularInline):
    model = CartItem
    extra = 0

# Inline for ProductSize
class ProductSizeInline(admin.TabularInline):
    model = ProductSize
    extra = 1
    readonly_fields = ('price', 'stock')

# Inline for ProductFilter
class ProductFilterInline(admin.TabularInline):
    model = ProductFilter
    extra = 1

# Inline for ProductSizeDiscount in ProductSize
class ProductSizeDiscountInline(admin.TabularInline):
    model = ProductSizeDiscount
    extra = 1
    readonly_fields = ('discounted_price',)

@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ('username', 'email', 'is_staff', 'is_active')
    search_fields = ('username', 'email')
    list_filter = ('is_staff', 'is_active')

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
    list_display = ('name', 'category', 'created_at', 'total_stock')
    list_filter = ('category', 'created_at')
    search_fields = ('name', 'description')
    inlines = [ProductSizeInline, ProductFilterInline]

    def total_stock(self, obj):
        return ProductSize.objects.filter(product=obj).aggregate(total=Sum('stock'))['total'] or 0
    total_stock.short_description = 'Total Stock'

@admin.register(ProductSize)
class ProductSizeAdmin(admin.ModelAdmin):
    list_display = ('product', 'size', 'price', 'stock', 'get_discounted_price')
    search_fields = ('product__name', 'size__name')
    list_filter = ('size',)
    inlines = [ProductSizeDiscountInline]

    def get_discounted_price(self, obj):
        discount = obj.discounts.filter(discount__is_active=True).first()
        return discount.discounted_price if discount else None
    get_discounted_price.short_description = 'Precio Descontado'

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'total', 'is_paid', 'is_shipped', 'created_at')
    list_filter = ('is_paid', 'is_shipped', 'created_at')
    search_fields = ('user__username',)
    readonly_fields = ('total', 'created_at', 'updated_at')
    inlines = [OrderItemInline]

@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ('order', 'product_size', 'quantity', 'price')
    search_fields = ('order__id', 'product_size__product__name')
    list_filter = ('order__created_at',)

@admin.register(Cart)
class CartAdmin(admin.ModelAdmin):
    list_display = ('user', 'created_at')
    search_fields = ('user__username',)
    inlines = [CartItemInline]

@admin.register(CartItem)
class CartItemAdmin(admin.ModelAdmin):
    list_display = ('cart', 'product_size', 'quantity')
    search_fields = ('cart__user__username', 'product_size__product__name')
    list_filter = ('cart__created_at',)

@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ('product', 'user', 'rating', 'created_at')
    list_filter = ('rating', 'created_at')
    search_fields = ('product__name', 'user__username')

@admin.register(Discount)
class DiscountAdmin(admin.ModelAdmin):
    list_display = ('name', 'discount_type', 'amount', 'start_date', 'end_date', 'is_active')
    list_filter = ('discount_type', 'is_active', 'start_date', 'end_date')
    search_fields = ('name',)

@admin.register(ProductSizeDiscount)
class ProductSizeDiscountAdmin(admin.ModelAdmin):
    list_display = ('product_size', 'discount', 'discounted_price')
    search_fields = ('product_size__product__name', 'discount__name')
    readonly_fields = ('discounted_price',)

@admin.register(Filter)
class FilterAdmin(admin.ModelAdmin):
    list_display = ('name', 'description')
    search_fields = ('name',)

@admin.register(ProductFilter)
class ProductFilterAdmin(admin.ModelAdmin):
    list_display = ('product', 'filter')
    search_fields = ('product__name', 'filter__name')
    list_filter = ('filter',)
