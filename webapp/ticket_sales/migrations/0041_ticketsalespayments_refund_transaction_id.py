# Generated by Django 4.2.15 on 2024-10-08 12:30

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('ticket_sales', '0040_terminalsettings_use_https'),
    ]

    operations = [
        migrations.AddField(
            model_name='ticketsalespayments',
            name='refund_transaction_id',
            field=models.CharField(blank=True, max_length=50, null=True, verbose_name='Идентификатор транзакции возврата'),
        ),
    ]
