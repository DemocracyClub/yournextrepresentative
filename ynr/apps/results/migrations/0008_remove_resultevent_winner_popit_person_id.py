from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [("results", "0007_update_winner_from_popit_person_id")]

    operations = [
        migrations.RemoveField(
            model_name="resultevent", name="winner_popit_person_id"
        )
    ]
