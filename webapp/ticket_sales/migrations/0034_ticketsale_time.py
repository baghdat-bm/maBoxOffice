# Generated by Django 4.2.15 on 2024-10-02 05:07

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('ticket_sales', '0033_ticketsalesticket_process_id'),
    ]

    operations = [
        migrations.AddField(
            model_name='ticketsale',
            name='time',
            field=models.TimeField(blank=True, null=True, verbose_name='Время'),
        ),
    ]