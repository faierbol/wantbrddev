# Generated by Django 2.0.2 on 2019-03-09 11:14

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('board', '0022_itemconnection_tags'),
    ]

    operations = [
        migrations.CreateModel(
            name='Communities',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100)),
                ('description', models.TextField(blank=True, default='')),
                ('slug', models.SlugField(default='', max_length=255)),
            ],
        ),
    ]