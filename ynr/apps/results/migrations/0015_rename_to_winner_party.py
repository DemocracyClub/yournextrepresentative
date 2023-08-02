from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [("results", "0014_rename_election_new_to_election")]

    operations = [
        migrations.RenameField(
            model_name="resultevent",
            old_name="winner_party_new",
            new_name="winner_party",
        )
    ]
