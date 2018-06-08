# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('comments', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='comments',
            name='rating',
            field=models.IntegerField(default=1, verbose_name='评分'),
        ),
        migrations.AddField(
            model_name='comments',
            name='title',
            field=models.CharField(max_length=20, default='', verbose_name='评论标题'),
        ),
    ]
