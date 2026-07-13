from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("candidates", "0095_ballot_timetable_fields"),
    ]

    operations = [
        migrations.RunPython(
            migrations.RunPython.noop, migrations.RunPython.noop
        )
    ]
