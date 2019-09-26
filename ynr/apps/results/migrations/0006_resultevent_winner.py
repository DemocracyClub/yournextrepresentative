from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("popolo", "0002_update_models_from_upstream"),
        ("results", "0005_auto_fill_election_and_post_name"),
    ]

    operations = [
        migrations.AddField(
            model_name="resultevent",
            name="winner",
            field=models.ForeignKey(
                default=1, to="popolo.Person", on_delete=models.CASCADE
            ),
            preserve_default=False,
        )
    ]
