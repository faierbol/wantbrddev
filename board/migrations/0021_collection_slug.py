# Generated by Django 2.0.2 on 2018-08-27 14:26

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('board', '0020_auto_20180827_1420'),
    ]

    operations = [
        migrations.AddField(
            model_name='collection',
            name='slug',
            field=models.SlugField(default='', max_length=255),
        ),
    ]
