# Generated by Django 2.0.2 on 2018-07-10 19:47

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('user', '0007_notification'),
    ]

    operations = [
        migrations.RenameField(
            model_name='notification',
            old_name='notfication_type',
            new_name='notification_type',
        ),
    ]
