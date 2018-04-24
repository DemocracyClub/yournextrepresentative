# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('uk_results', '0031_remove_postresult_post'),
    ]

    operations = [
        migrations.RenameModel(
            'PostResult',
            'PostElectionResult'),
    ]
