# -*- coding: utf-8 -*-
# Generated by Django 1.11.1 on 2017-10-12 15:05
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('piremote', '0020_auto_20170622_1752'),
    ]

    operations = [
        migrations.AddField(
            model_name='rating',
            name='filesize',
            field=models.IntegerField(default=0),
        ),
    ]
