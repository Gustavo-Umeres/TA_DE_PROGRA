# Generated by Django 5.1.3 on 2024-11-14 03:22

import cloudinary_storage.storage
import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('appproject', '0007_remove_productfilter_value'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='product',
            name='image',
        ),
        migrations.CreateModel(
            name='FilterValue',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('value', models.CharField(max_length=50)),
                ('filter', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='values', to='appproject.filter')),
            ],
        ),
        migrations.CreateModel(
            name='ProductFilterValue',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('filter_value', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='products', to='appproject.filtervalue')),
                ('product', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='filter_values', to='appproject.product')),
            ],
        ),
        migrations.CreateModel(
            name='ProductImage',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('image', models.ImageField(storage=cloudinary_storage.storage.MediaCloudinaryStorage(), upload_to='products/')),
                ('product', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='images', to='appproject.product')),
            ],
        ),
        migrations.DeleteModel(
            name='ProductFilter',
        ),
    ]
