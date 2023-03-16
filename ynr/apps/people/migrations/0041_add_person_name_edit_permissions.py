from auth_helpers.migrations import (
    get_migration_group_create,
    get_migration_group_delete,
)
from django.db import migrations
from people.models import TRUSTED_TO_EDIT_NAME


class Migration(migrations.Migration):

    dependencies = [("people", "0040_auto_20220511_1222")]

    operations = [
        migrations.RunPython(
            get_migration_group_create(
                TRUSTED_TO_EDIT_NAME, ["can_edit_person_name"]
            ),
            get_migration_group_delete(TRUSTED_TO_EDIT_NAME),
        )
    ]
