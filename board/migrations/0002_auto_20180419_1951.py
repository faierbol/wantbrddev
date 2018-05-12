# Generated by Django 2.0.2 on 2018-04-19 19:51

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('board', '0001_initial'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='board',
            name='content_type',
        ),
        migrations.AddField(
            model_name='board',
            name='description',
            field=models.TextField(blank=True, default='', max_length=500),
        ),
        migrations.AddField(
            model_name='board',
            name='slug',
            field=models.SlugField(default=''),
        ),
        migrations.AddField(
            model_name='item',
            name='allow_comments',
            field=models.BooleanField(default=True, verbose_name='allow comments'),
        ),
        migrations.AlterField(
            model_name='board',
            name='board_type',
            field=models.CharField(choices=[('Want', 'Wants'), ('Recommended', 'Recommended')], default='Want', max_length=11),
        ),
    ]
