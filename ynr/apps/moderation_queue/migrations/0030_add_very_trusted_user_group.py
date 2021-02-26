from django.db import migrations

from moderation_queue.models import VERY_TRUSTED_USER_GROUP_NAME


def add_group(apps, schema_editor):
    Group = apps.get_model("auth", "Group")
    Group.objects.update_or_create(name=VERY_TRUSTED_USER_GROUP_NAME)


def remove_group(apps, schema_editor):
    Group = apps.get_model("auth", "Group")
    try:
        Group.objects.get(name=VERY_TRUSTED_USER_GROUP_NAME).delete()
    except Group.DoesNotExist:
        pass


class Migration(migrations.Migration):
    dependencies = [("moderation_queue", "0029_update_image_upload_to")]

    operations = [migrations.RunPython(add_group, remove_group)]
