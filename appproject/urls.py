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
    path('add_product/', views.add_product, name='add_product'),
    path('edit_product/<int:product_id>/', views.edit_product, name='edit_product'),

    path('add_to_cart/<int:product_id>/', views.add_to_cart, name='add_to_cart'),  # Nueva URL
    path('cart/', views.view_cart, name='view_cart'),  # Cambié a view_cart
    path('checkout/', views.checkout_view, name='checkout'),
    path('register/', views.register, name='register'),

        # Asegúrate de que las siguientes líneas estén presentes
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'), 
    path('add_review/<int:product_id>/', views.add_review, name='add_review'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)