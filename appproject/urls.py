from django.urls import path
from django.contrib.auth import views as auth_views
from . import views
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('', views.home, name='home'),
    path('about/', views.about, name='about'), 
    path('products/', views.products_list, name='products_list'),
    path('product/<int:product_id>/', views.product_detail, name='product_detail'),
    path('add_product_to_cart/', views.add_product_to_cart, name='add_product_to_cart'),
    path('edit_product/<int:product_id>/', views.edit_product, name='edit_product'),

    path('profile/', views.profile_view, name='profile'),

    path('cart/update/', views.update_cart, name='update_cart'),  # Nueva ruta para actualizar el carrito


    # URL para agregar un producto al carrito
    path('add_to_cart/<int:product_id>/', views.add_to_cart, name='add_to_cart'),
    
    # URL para ver el carrito
    path('cart/', views.view_cart, name='view_cart'),
    
    # URL para el proceso de checkout
    path('checkout/', views.checkout_view, name='checkout'),

    
    # URL para registro de usuarios
    path('register/', views.register, name='register'),
    
    # Asegúrate de que las siguientes líneas estén presentes
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'), 
    
    # URL para agregar revisiones de productos
    path('add_review/<int:product_id>/', views.add_review, name='add_review'),


    path('procesar_pago/', views.procesar_pago, name='procesar_pago'),
    path('pagos/exito/', views.pago_exito, name='pago_exito'),
    path('pagos/fallo/', views.pago_fallo, name='pago_fallo'),
    path('pagos/pendiente/', views.pago_pendiente, name='pago_pendiente'),
]

# Manejo de archivos estáticos y medios en modo de desarrollo
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
