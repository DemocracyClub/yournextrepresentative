from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("popolo", "0002_update_models_from_upstream"),
        ("results", "0009_resultevent_election_new"),
    ]

    operations = [
        migrations.AddField(
            model_name="resultevent",
            name="winner_party_new",
            field=models.ForeignKey(
                blank=True,
                to="popolo.Organization",
                null=True,
                on_delete=models.CASCADE,
            ),
        )
    ]
