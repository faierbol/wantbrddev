# Generated by Django 2.0.2 on 2018-07-11 13:32

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('user', '0010_notification_created'),
    ]

    operations = [
        migrations.AlterField(
            model_name='notification',
            name='board_ref',
            field=models.IntegerField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='notification',
            name='item_ref',
            field=models.IntegerField(blank=True, null=True),
        ),
    ]
