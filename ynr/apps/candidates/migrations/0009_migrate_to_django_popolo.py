from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        (
            "candidates",
            "0008_membershipextra_organizationextra_personextra_postextra",
        ),
        ("popolo", "0002_update_models_from_upstream"),
    ]

    operations = [
        migrations.RunPython(
            migrations.RunPython.noop, migrations.RunPython.noop
        )
    ]
