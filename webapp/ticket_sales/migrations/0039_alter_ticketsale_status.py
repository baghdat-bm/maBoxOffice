# Generated by Django 4.2.15 on 2024-10-07 10:33

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('ticket_sales', '0038_ticketsalesticket_refund_amount'),
    ]

    operations = [
        migrations.AlterField(
            model_name='ticketsale',
            name='status',
            field=models.CharField(blank=True, choices=[('NP', 'Не оплачен'), ('PD', 'Оплачен'), ('PP', 'Частично оплачен'), ('RT', 'Возврат'), ('PT', 'Частичный возврат'), ('CN', 'Отменен'), ('IS', 'Оформлен')], default='NP', max_length=2, null=True, verbose_name='Статус'),
        ),
    ]