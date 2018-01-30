# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('results', '0012_migrate_resultevent_data'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='resultevent',
            name='election',
        ),
        migrations.RemoveField(
            model_name='resultevent',
            name='winner_party_id',
        ),
        migrations.RemoveField(
            model_name='resultevent',
            name='winner_person_name',
        ),
    ]
