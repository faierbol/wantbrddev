# Generated by Django 2.0.2 on 2019-03-30 10:42

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('user', '0016_auto_20190102_1204'),
    ]

    operations = [
        migrations.AddField(
            model_name='profile',
            name='user_type',
            field=models.CharField(choices=[('PERSONAL', 'Personal'), ('PRO', 'Pro'), ('BUSINESS', 'Business')], default='PERSONAL', max_length=8),
        ),
    ]
