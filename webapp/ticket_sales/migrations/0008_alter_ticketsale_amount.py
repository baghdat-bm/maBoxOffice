# Generated by Django 4.2.15 on 2024-08-16 10:14

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('ticket_sales', '0007_alter_ticketsale_status'),
    ]

    operations = [
        migrations.AlterField(
            model_name='ticketsale',
            name='amount',
            field=models.IntegerField(blank=True, default=0, verbose_name='Сумма итого'),
        ),
    ]