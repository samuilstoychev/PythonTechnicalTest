# Generated by Django 2.2.13 on 2020-12-13 23:13

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('bonds', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='bond',
            name='lei',
            field=models.CharField(max_length=20),
        ),
    ]