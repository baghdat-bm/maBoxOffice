# Generated by Django 4.2.15 on 2024-08-15 04:03

import datetime
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('ticket_sales', '0002_alter_ticketsalespayments_ticket_sale_and_more'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='ticketsalespayments',
            name='accepted_amount',
        ),
        migrations.RemoveField(
            model_name='ticketsalespayments',
            name='accepted_from_the_buyer',
        ),
        migrations.RemoveField(
            model_name='ticketsalespayments',
            name='amount_of_change',
        ),
        migrations.AddField(
            model_name='ticketsalespayments',
            name='amount',
            field=models.IntegerField(blank=True, default=0, verbose_name='Сумма оплаты'),
        ),
        migrations.AlterField(
            model_name='ticketsalespayments',
            name='process_id',
            field=models.CharField(default=datetime.datetime(2024, 8, 15, 9, 3, 38, 481205), max_length=20, unique=True, verbose_name='Идентификатор процесса'),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='ticketsalesservice',
            name='inventories_count',
            field=models.PositiveSmallIntegerField(verbose_name='Количество инвентаря'),
        ),
    ]