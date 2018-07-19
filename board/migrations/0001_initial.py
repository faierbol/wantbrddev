# Generated by Django 2.0.2 on 2018-07-19 14:32

import board.models
from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import sorl.thumbnail.fields
import taggit.managers


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('taggit', '0002_auto_20150616_2121'),
    ]

    operations = [
        migrations.CreateModel(
            name='Board',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('board_name', models.CharField(max_length=255)),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('private', models.BooleanField(default=False)),
                ('description', models.TextField(blank=True, default='', max_length=500)),
                ('video', models.CharField(blank=True, max_length=50)),
                ('hero', models.ImageField(blank=True, null=True, upload_to=board.models.user_directory_path)),
                ('show_video', models.BooleanField(default=False)),
                ('active', models.BooleanField(default=False)),
                ('slug', models.SlugField(default='')),
                ('deleteable', models.BooleanField(default=True)),
                ('recommended', models.BooleanField(default=False)),
                ('tags', taggit.managers.TaggableManager(blank=True, help_text='A comma-separated list of tags.', through='taggit.TaggedItem', to='taggit.Tag', verbose_name='Tags')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='BoardLike',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('board', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='board.Board')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='BoardPrivacy',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('board', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='board.Board')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='BoardView',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('ip', models.CharField(max_length=16)),
                ('board', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='board.Board')),
            ],
        ),
        migrations.CreateModel(
            name='Item',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('item_name', models.CharField(max_length=255)),
            ],
        ),
        migrations.CreateModel(
            name='ItemConnection',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('image', sorl.thumbnail.fields.ImageField(default='defaults/no-item.png', upload_to='uploads/items/')),
                ('img_own', models.BooleanField(default=False)),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('allow_comments', models.BooleanField(default=True, verbose_name='allow comments')),
                ('purchase_url', models.URLField(blank=True, max_length=255)),
                ('original_purchase_url', models.URLField(blank=True, max_length=255)),
                ('item_desc', models.CharField(blank=True, max_length=500, null=True)),
                ('review', models.CharField(blank=True, default='', max_length=500, null=True)),
                ('rating', models.CharField(default=0, max_length=500)),
                ('item_status', models.CharField(choices=[('WNT', 'I want this'), ('GOT', "I've got this")], default='WNT', max_length=3)),
                ('active', models.BooleanField(default=True)),
                ('board', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='board.Board')),
                ('item', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='board.Item')),
            ],
        ),
        migrations.CreateModel(
            name='ItemLike',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('item_conx', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='board.ItemConnection')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='ItemView',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('ip', models.CharField(max_length=16)),
                ('item_conx', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='board.ItemConnection')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to=settings.AUTH_USER_MODEL)),
            ],
        ),
    ]
