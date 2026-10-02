from auth_helpers.migrations import (
    get_migration_group_create,
    get_migration_group_delete,
)
from django.db import migrations
from splitting.models import TRUSTED_TO_SPLIT_GROUP_NAME


class Migration(migrations.Migration):
    dependencies = [("auth", "0012_alter_user_first_name_max_length")]

    operations = [
        migrations.RunPython(
            get_migration_group_create(TRUSTED_TO_SPLIT_GROUP_NAME, []),
            get_migration_group_delete(TRUSTED_TO_SPLIT_GROUP_NAME),
        )
    ]
