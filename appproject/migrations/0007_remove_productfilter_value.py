# Generated by Django 5.1.3 on 2024-11-10 19:47

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('appproject', '0006_delete_favorite'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='productfilter',
            name='value',
        ),
    ]
