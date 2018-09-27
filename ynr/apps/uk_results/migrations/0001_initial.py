from django.db import migrations, models
from django.conf import settings
import django_extensions.db.fields


class Migration(migrations.Migration):

    dependencies = [
        ("popolo", "0002_update_models_from_upstream"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="CandidateResult",
            fields=[
                (
                    "id",
                    models.AutoField(
                        verbose_name="ID",
                        serialize=False,
                        auto_created=True,
                        primary_key=True,
                    ),
                ),
                (
                    "created",
                    django_extensions.db.fields.CreationDateTimeField(
                        auto_now_add=True, verbose_name="created"
                    ),
                ),
                (
                    "modified",
                    django_extensions.db.fields.ModificationDateTimeField(
                        auto_now=True, verbose_name="modified"
                    ),
                ),
                ("num_ballots_reported", models.IntegerField()),
                ("is_winner", models.BooleanField(default=False)),
                (
                    "person",
                    models.ForeignKey(
                        related_name="candidate_results",
                        to="popolo.Person",
                        on_delete=models.CASCADE,
                    ),
                ),
            ],
            options={"ordering": ("person",)},
        ),
        migrations.CreateModel(
            name="ResultSet",
            fields=[
                (
                    "id",
                    models.AutoField(
                        verbose_name="ID",
                        serialize=False,
                        auto_created=True,
                        primary_key=True,
                    ),
                ),
                (
                    "created",
                    django_extensions.db.fields.CreationDateTimeField(
                        auto_now_add=True, verbose_name="created"
                    ),
                ),
                (
                    "modified",
                    django_extensions.db.fields.ModificationDateTimeField(
                        auto_now=True, verbose_name="modified"
                    ),
                ),
                ("num_turnout_reported", models.IntegerField()),
                ("num_spoilt_ballots", models.IntegerField()),
                ("is_final", models.BooleanField(default=False)),
                ("source", models.TextField()),
                ("ip_address", models.GenericIPAddressField()),
                (
                    "confirmed_by",
                    models.ForeignKey(
                        related_name="result_sets_confirmed",
                        to=settings.AUTH_USER_MODEL,
                        null=True,
                        on_delete=models.CASCADE,
                    ),
                ),
                (
                    "post",
                    models.ForeignKey(
                        related_name="result_sets",
                        to="popolo.Post",
                        on_delete=models.CASCADE,
                    ),
                ),
                (
                    "user",
                    models.ForeignKey(
                        related_name="result_sets",
                        to=settings.AUTH_USER_MODEL,
                        null=True,
                        on_delete=models.CASCADE,
                    ),
                ),
            ],
            options={
                "ordering": ("-modified", "-created"),
                "abstract": False,
                "get_latest_by": "modified",
            },
        ),
        migrations.AddField(
            model_name="candidateresult",
            name="result_set",
            field=models.ForeignKey(
                related_name="candidate_results",
                to="uk_results.ResultSet",
                on_delete=models.CASCADE,
            ),
        ),
        migrations.AlterUniqueTogether(
            name="candidateresult", unique_together={("result_set", "person")}
        ),
    ]
