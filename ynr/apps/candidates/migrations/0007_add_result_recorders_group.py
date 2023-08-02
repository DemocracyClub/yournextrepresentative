from auth_helpers.migrations import (
    get_migration_group_create,
    get_migration_group_delete,
)
from candidates.models import RESULT_RECORDERS_GROUP_NAME
from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [("candidates", "0006_auto_add_trusted_to_rename_group")]

    operations = [
        migrations.RunPython(
            get_migration_group_create(RESULT_RECORDERS_GROUP_NAME, []),
            get_migration_group_delete(RESULT_RECORDERS_GROUP_NAME),
        )
    ]
