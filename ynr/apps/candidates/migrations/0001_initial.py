from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [migrations.swappable_dependency(settings.AUTH_USER_MODEL)]

    operations = [
        migrations.CreateModel(
            name="LoggedAction",
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
                ("action_type", models.CharField(max_length=64)),
                ("popit_person_new_version", models.CharField(max_length=32)),
                ("popit_person_id", models.CharField(max_length=256)),
                ("created", models.DateTimeField(auto_now_add=True)),
                ("updated", models.DateTimeField(auto_now=True)),
                (
                    "ip_address",
                    models.CharField(max_length=50, null=True, blank=True),
                ),
                ("source", models.TextField()),
                (
                    "user",
                    models.ForeignKey(
                        blank=True,
                        to=settings.AUTH_USER_MODEL,
                        null=True,
                        on_delete=models.CASCADE,
                    ),
                ),
            ],
            options={},
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name="MaxPopItIds",
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
                ("popit_collection_name", models.CharField(max_length=255)),
                ("max_id", models.IntegerField(default=0)),
            ],
            options={},
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name="PersonRedirect",
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
                ("old_person_id", models.IntegerField()),
                ("new_person_id", models.IntegerField()),
            ],
            options={},
            bases=(models.Model,),
        ),
    ]
