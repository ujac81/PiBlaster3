# -*- coding: utf-8 -*-
# Generated by Django 1.11.1 on 2017-05-19 14:34
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('piremote', '0015_auto_20170519_1619'),
    ]

    operations = [
        migrations.AlterField(
            model_name='smartplaylistitem',
            name='itemtype',
            field=models.PositiveSmallIntegerField(choices=[(0, 'empty'), (1, 'Rating greater or equal'), (2, 'Rating equal'), (3, 'Path is one of'), (12, 'Is in playlist'), (4, 'Genre is one of'), (5, 'Artist is one of'), (6, 'Year less or equal'), (7, 'Year greater or equal'), (8, 'Prevent intros'), (9, 'Prevent duplicates'), (10, 'Not played last 24 hours'), (11, 'Prevent live songs')], default=0),
        ),
    ]
