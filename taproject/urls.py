from django.contrib import admin
from django.urls import path, include  # Asegúrate de incluir esto

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('appproject.urls')),  # Incluye tus rutas aquí
]
