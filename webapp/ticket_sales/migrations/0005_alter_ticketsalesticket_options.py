# Generated by Django 4.2.15 on 2024-09-04 01:27

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('ticket_sales', '0004_ticketsalesticket_number'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='ticketsalesticket',
            options={'ordering': ['number'], 'verbose_name': 'Билет', 'verbose_name_plural': 'Билеты'},
        ),
    ]