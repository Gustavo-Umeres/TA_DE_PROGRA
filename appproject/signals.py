# signals.py
from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import User, Cart

@receiver(post_save, sender=User)
def save_user_cart(sender, instance, created, **kwargs):
    if created:  # Solo se ejecuta si se ha creado un nuevo usuario
        Cart.objects.create(user=instance)
