# Generated by Django 3.2.3 on 2024-09-19 14:42

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('recipes', '0009_auto_20240918_2005'),
    ]

    operations = [
        migrations.AlterField(
            model_name='ingredient',
            name='name',
            field=models.CharField(max_length=100, unique=True, verbose_name='Название ингредиента'),
        ),
    ]
