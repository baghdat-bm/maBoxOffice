# Generated by Django 4.2.15 on 2024-10-11 12:25

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('ticket_sales', '0044_remove_ticketsale_tickets_made'),
    ]

    operations = [
        migrations.AddField(
            model_name='ticketsalesticket',
            name='activated_date',
            field=models.DateTimeField(blank=True, null=True, verbose_name='Дата активации'),
        ),
    ]