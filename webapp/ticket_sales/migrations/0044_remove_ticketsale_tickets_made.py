# Generated by Django 4.2.15 on 2024-10-10 05:32

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('ticket_sales', '0043_alter_appsettings_minutes_after_and_more'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='ticketsale',
            name='tickets_made',
        ),
    ]