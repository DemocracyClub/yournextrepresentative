# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations

from auth_helpers.migrations import (
    get_migration_group_create,
    get_migration_group_delete,
)
from candidates.models import TRUSTED_TO_REVIEW_CHANGES_GROUP_NAME


class Migration(migrations.Migration):

    dependencies = [
        ('candidates', '0033_changereviewed'),
    ]

    operations = [
        migrations.RunPython(
            get_migration_group_create(TRUSTED_TO_REVIEW_CHANGES_GROUP_NAME, []),
            get_migration_group_delete(TRUSTED_TO_REVIEW_CHANGES_GROUP_NAME),
        )
    ]
