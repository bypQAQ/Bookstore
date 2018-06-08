# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('books', '0002_auto_20180402_1152'),
    ]

    operations = [
        migrations.RenameField(
            model_name='books',
            old_name='unite',
            new_name='unit',
        ),
        migrations.RenameField(
            model_name='books',
            old_name='updata_time',
            new_name='update_time',
        ),
    ]
