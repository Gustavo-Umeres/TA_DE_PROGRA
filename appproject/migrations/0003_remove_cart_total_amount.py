# Generated by Django 5.1.2 on 2024-10-20 05:25

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('appproject', '0002_cart_total_amount'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='cart',
            name='total_amount',
        ),
    ]
