from django.db import migrations


def fix_territory(apps, schema_editor):
    Post = apps.get_model("popolo", "Post")
    Post.objects.exclude(
        territory_code__in=["ENG", "WLS", "NIR", "SCT"]
    ).update(territory_code="ENG")


class Migration(migrations.Migration):
    dependencies = [
        ("popolo", "0051_alter_membership_deselected_and_more"),
    ]

    operations = [
        migrations.RunPython(
            code=fix_territory, reverse_code=migrations.RunPython.noop
        )
    ]
