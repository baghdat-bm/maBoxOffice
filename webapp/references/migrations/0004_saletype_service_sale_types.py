# Generated by Django 4.2.15 on 2024-10-01 09:26

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('references', '0003_alter_event_options_alter_eventtemplate_options'),
    ]

    operations = [
        migrations.CreateModel(
            name='SaleType',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('code', models.CharField(max_length=2, unique=True)),
                ('name', models.CharField(max_length=100)),
            ],
        ),
        migrations.AddField(
            model_name='service',
            name='sale_types',
            field=models.ManyToManyField(default=None, to='references.saletype', verbose_name='Виды продаж'),
        ),
    ]