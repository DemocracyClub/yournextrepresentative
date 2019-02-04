from django.db import connection, migrations


class Migration(migrations.Migration):

    dependencies = [
        (
            "candidates",
            "0008_membershipextra_organizationextra_personextra_postextra",
        ),
        ("images", "0001_initial"),
        ("popolo", "0002_update_models_from_upstream"),
    ]

    operations = [
        migrations.RunPython(
            migrations.RunPython.noop, migrations.RunPython.noop
        )
    ]
