# Generated by Django 4.2.15 on 2024-09-03 05:58

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('references', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='event',
            name='begin_date',
            field=models.DateField(verbose_name='Дата начала'),
        ),
        migrations.AlterField(
            model_name='event',
            name='end_date',
            field=models.DateField(verbose_name='Дата окончания'),
        ),
    ]
