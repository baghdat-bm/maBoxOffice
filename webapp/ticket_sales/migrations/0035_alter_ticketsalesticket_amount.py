# Generated by Django 4.2.15 on 2024-10-02 11:12

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('ticket_sales', '0034_ticketsale_time'),
    ]

    operations = [
        migrations.AlterField(
            model_name='ticketsalesticket',
            name='amount',
            field=models.IntegerField(blank=True, null=True, verbose_name='Сумма билета'),
        ),
    ]