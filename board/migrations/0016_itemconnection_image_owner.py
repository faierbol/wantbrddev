# Generated by Django 2.0.2 on 2018-08-14 19:55

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('board', '0015_itemconnection_itook'),
    ]

    operations = [
        migrations.AddField(
            model_name='itemconnection',
            name='image_owner',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
    ]
