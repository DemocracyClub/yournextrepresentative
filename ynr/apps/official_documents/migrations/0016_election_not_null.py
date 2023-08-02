from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("official_documents", "0015_rename_election_model_to_election")
    ]

    operations = [
        migrations.AlterField(
            model_name="officialdocument",
            name="election",
            field=models.ForeignKey(
                to="elections.Election", on_delete=models.CASCADE
            ),
        )
    ]
