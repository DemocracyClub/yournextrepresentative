from django.db import migrations

from django.contrib.auth.management import create_permissions

TRUSTED_TO_RENAME_GROUP_NAME = "Trusted To Rename"


def add_trusted_to_rename_group(apps, schema_editor, create_if_missing=True):
    group_name, permission_codenames = TRUSTED_TO_RENAME_GROUP_NAME, []
    Permission = apps.get_model("auth", "Permission")
    Group = apps.get_model("auth", "Group")
    try:
        permissions = Permission.objects.filter(
            codename__in=permission_codenames
        )
    except Permission.DoesNotExist:
        if create_if_missing:
            # This is a way of making sure the permissions exist taken from:
            # https://code.djangoproject.com/ticket/23422#comment:6
            assert not getattr(apps, "models_module", None)
            apps.models_module = True
            create_permissions(apps, verbosity=0)
            apps.models_module = None
            return add_trusted_to_rename_group(
                apps, schema_editor, create_if_missing=False
            )
        else:
            raise
    new_group = Group.objects.create(name=group_name)
    for permission in permissions:
        new_group.permissions.add(permission)


def remove_trusted_to_rename_group(apps, schema_editor):

    Group = apps.get_model("auth", "Group")
    Group.objects.get(name=TRUSTED_TO_RENAME_GROUP_NAME).delete()


class Migration(migrations.Migration):

    dependencies = [("candidates", "0005_add_trusted_to_lock_group")]

    operations = [
        migrations.RunPython(
            add_trusted_to_rename_group, remove_trusted_to_rename_group
        )
    ]
