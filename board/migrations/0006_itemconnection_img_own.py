# Generated by Django 2.0.2 on 2018-07-15 14:45

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('board', '0005_itemconnection_original_purchase_url'),
    ]

    operations = [
        migrations.AddField(
            model_name='itemconnection',
            name='img_own',
            field=models.BooleanField(default=False),
        ),
    ]