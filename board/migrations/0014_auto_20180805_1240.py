# Generated by Django 2.0.2 on 2018-08-05 12:40

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('board', '0013_auto_20180805_1224'),
    ]

    operations = [
        migrations.AlterField(
            model_name='itemconnection',
            name='slug',
            field=models.SlugField(default='', max_length=255),
        ),
    ]