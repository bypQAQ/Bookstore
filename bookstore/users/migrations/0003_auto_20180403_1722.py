# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0002_auto_20180402_1242'),
    ]

    operations = [
        migrations.AlterField(
            model_name='passport',
            name='username',
            field=models.CharField(unique=True, max_length=20, verbose_name='用户名称'),
        ),
    ]
