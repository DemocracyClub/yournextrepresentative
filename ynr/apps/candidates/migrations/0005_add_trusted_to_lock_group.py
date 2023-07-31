from auth_helpers.migrations import (
    get_migration_group_create,
    get_migration_group_delete,
)
from candidates.models import TRUSTED_TO_LOCK_GROUP_NAME
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [("candidates", "0004_add_trusted_to_merge_group")]

    operations = [
        migrations.RunPython(
            get_migration_group_create(TRUSTED_TO_LOCK_GROUP_NAME, []),
            get_migration_group_delete(TRUSTED_TO_LOCK_GROUP_NAME),
        )
    ]
