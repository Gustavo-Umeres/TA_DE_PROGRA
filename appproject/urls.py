from django.urls import path
from . import views
from django.conf import settings
from django.conf.urls.static import static

# Vistas principales
urlpatterns = [
    # Página de inicio y sobre nosotros
    path('', views.home, name='home'),  # Página de inicio
    path('about/', views.about, name='about'),  # Página 'Sobre Nosotros'

    # Gestión de productos
    path('products/', views.products_list, name='products_list'),  # Listado de productos
    path('product/<int:product_id>/', views.product_detail, name='product_detail'),  # Detalles de un producto específico
    path('category/<int:category_id>/', views.products_by_category, name='products_by_category'),  # Filtrado de productos por categoría

    # Búsquedas
    path('products/search/', views.search_products, name='search_products'),  # Búsqueda en tiempo real de productos

    # Carrito de compras
    path('add_to_cart/<int:product_id>/', views.add_to_cart, name='add_to_cart'),  # Añadir producto al carrito
    path('cart/', views.view_cart, name='view_cart'),  # Vista del carrito
    path('cart/update/', views.update_cart, name='update_cart'),  # Actualizar carrito (añadir, eliminar, etc.)
    
    # Proceso de compra
    path('checkout/', views.checkout_view, name='checkout'),  # Vista del proceso de checkout
    path('procesar_pago/', views.procesar_pago, name='procesar_pago'),  # Procesar pago con Mercado Pago
    path('pagos/exito/', views.pago_exito, name='pago_exito'),  # Vista de éxito de pago
    path('pagos/fallo/', views.pago_fallo, name='pago_fallo'),  # Vista de fallo de pago
    path('pagos/pendiente/', views.pago_pendiente, name='pago_pendiente'),  # Vista de pago pendiente

    # Gestión de usuarios
    path('register/', views.register, name='register'),  # Registro de usuarios
    path('login/', views.login_view, name='login'),  # Inicio de sesión
    path('logout/', views.logout_view, name='logout'),  # Cierre de sesión
    path('profile/', views.profile_view, name='profile'),  # Vista de perfil de usuario
    
    # Reseñas de productos
    path('add_review/<int:product_id>/', views.add_review, name='add_review'),  # Añadir una reseña de producto

    # Administración de productos (solo para administradores)
    path('add_product_to_cart/', views.add_product_to_cart, name='add_product_to_cart'),  # Agregar producto al carrito
    path('edit_product/<int:product_id>/', views.edit_product, name='edit_product'),  # Editar un producto
]

# Manejo de archivos estáticos y de media en modo de desarrollo
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
