# Generated by Django 2.0.2 on 2018-04-23 20:02

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('board', '0004_board_show_video'),
    ]

    operations = [
        migrations.AlterField(
            model_name='boardview',
            name='board',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='board.Board'),
        ),
    ]
