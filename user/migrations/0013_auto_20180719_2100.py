# Generated by Django 2.0.2 on 2018-07-19 21:00

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('user', '0012_auto_20180719_2057'),
    ]

    operations = [
        migrations.AlterField(
            model_name='profile',
            name='bio',
            field=models.TextField(blank=True, default='', max_length=500),
        ),
    ]
