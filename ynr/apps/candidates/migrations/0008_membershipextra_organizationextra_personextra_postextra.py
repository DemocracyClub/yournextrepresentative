from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("popolo", "0002_update_models_from_upstream"),
        ("elections", "0003_allow_null_winner_membership_role"),
        ("candidates", "0007_add_result_recorders_group"),
    ]

    operations = [
        migrations.CreateModel(
            name="MembershipExtra",
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
                    "base",
                    models.OneToOneField(
                        related_name="extra",
                        to="popolo.Membership",
                        on_delete=models.CASCADE,
                    ),
                ),
                (
                    "election",
                    models.ForeignKey(
                        related_name="candidacies",
                        blank=True,
                        to="elections.Election",
                        null=True,
                        on_delete=models.CASCADE,
                    ),
                ),
                ("party_list_position", models.IntegerField(null=True)),
                ("elected", models.NullBooleanField()),
            ],
        ),
        migrations.CreateModel(
            name="OrganizationExtra",
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
                ("register", models.CharField(max_length=512, blank=True)),
                (
                    "base",
                    models.OneToOneField(
                        related_name="extra",
                        to="popolo.Organization",
                        on_delete=models.CASCADE,
                    ),
                ),
                ("slug", models.CharField(max_length=256, blank=True)),
            ],
        ),
        migrations.CreateModel(
            name="PersonExtra",
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
                ("cv", models.TextField(blank=True)),
                ("program", models.TextField(blank=True)),
                ("versions", models.TextField(blank=True)),
                (
                    "base",
                    models.OneToOneField(
                        related_name="extra",
                        to="popolo.Person",
                        on_delete=models.CASCADE,
                    ),
                ),
                (
                    "not_standing",
                    models.ManyToManyField(
                        related_name="persons_not_standing",
                        to="elections.Election",
                    ),
                ),
            ],
        ),
        migrations.CreateModel(
            name="PartySet",
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
                ("slug", models.CharField(max_length=256)),
                ("name", models.CharField(max_length=1024)),
                (
                    "parties",
                    models.ManyToManyField(
                        related_name="party_sets", to="popolo.Organization"
                    ),
                ),
            ],
        ),
        migrations.CreateModel(
            name="PostExtra",
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
                    "base",
                    models.OneToOneField(
                        related_name="extra",
                        to="popolo.Post",
                        on_delete=models.CASCADE,
                    ),
                ),
                ("slug", models.CharField(max_length=256, blank=True)),
                ("candidates_locked", models.BooleanField(default=False)),
                (
                    "elections",
                    models.ManyToManyField(
                        related_name="posts", to="elections.Election"
                    ),
                ),
                ("group", models.CharField(max_length=1024, blank=True)),
                (
                    "party_set",
                    models.ForeignKey(
                        blank=True,
                        to="candidates.PartySet",
                        null=True,
                        on_delete=models.CASCADE,
                    ),
                ),
            ],
        ),
        migrations.CreateModel(
            name="AreaExtra",
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
                    "base",
                    models.OneToOneField(
                        related_name="extra",
                        to="popolo.Area",
                        on_delete=models.CASCADE,
                    ),
                ),
                (
                    "type",
                    models.ForeignKey(
                        related_name="areas",
                        blank=True,
                        to="elections.AreaType",
                        null=True,
                        on_delete=models.CASCADE,
                    ),
                ),
            ],
        ),
    ]
