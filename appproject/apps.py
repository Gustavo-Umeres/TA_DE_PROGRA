# appproject/apps.py
from django.apps import AppConfig

class AppprojectConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'appproject'

    def ready(self):
        import appproject.signals  # Importar el módulo de señales
