# Generated by Django 2.0.2 on 2018-08-13 20:14

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('board', '0014_auto_20180805_1240'),
    ]

    operations = [
        migrations.AddField(
            model_name='itemconnection',
            name='itook',
            field=models.BooleanField(default=False),
        ),
    ]
