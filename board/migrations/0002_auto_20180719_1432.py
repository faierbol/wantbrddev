# Generated by Django 2.0.2 on 2018-07-19 14:32

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('board', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='board',
            name='description',
            field=models.TextField(blank=True, default='', max_length=1000),
        ),
    ]
