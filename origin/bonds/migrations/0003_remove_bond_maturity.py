# Generated by Django 2.2.13 on 2020-12-12 00:13

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('bonds', '0002_auto_20201212_0007'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='bond',
            name='maturity',
        ),
    ]