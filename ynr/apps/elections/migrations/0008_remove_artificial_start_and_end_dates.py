from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("elections", "0007_rename_new_organization_to_organization")
    ]

    operations = [
        migrations.RemoveField(
            model_name="election", name="candidacy_start_date"
        ),
        migrations.RemoveField(
            model_name="election", name="party_membership_end_date"
        ),
        migrations.RemoveField(
            model_name="election", name="party_membership_start_date"
        ),
    ]
