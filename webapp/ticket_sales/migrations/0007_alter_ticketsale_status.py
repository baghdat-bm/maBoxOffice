# Generated by Django 4.2.15 on 2024-08-16 10:13

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('ticket_sales', '0006_alter_ticketsale_date'),
    ]

    operations = [
        migrations.AlterField(
            model_name='ticketsale',
            name='status',
            field=models.CharField(blank=True, default='Сформирован', max_length=15, null=True, verbose_name='Статус'),
        ),
    ]