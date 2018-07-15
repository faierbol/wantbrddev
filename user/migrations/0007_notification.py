# Generated by Django 2.0.2 on 2018-07-10 19:18

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('user', '0006_profile_login_count'),
    ]

    operations = [
        migrations.CreateModel(
            name='Notification',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('notfication_type', models.CharField(default='', max_length=500)),
                ('seen', models.BooleanField(default=False)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='user_notify_set', to=settings.AUTH_USER_MODEL)),
                ('user_trigger', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='user_trigger_set', to=settings.AUTH_USER_MODEL)),
            ],
        ),
    ]