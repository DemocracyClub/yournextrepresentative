from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = []

    operations = [
        migrations.CreateModel(
            name="CachedCount",
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
                ("count_type", models.CharField(max_length=100, db_index=True)),
                ("name", models.CharField(max_length=100)),
                ("count", models.IntegerField()),
                ("object_id", models.CharField(max_length=100, blank=True)),
            ],
            options={"ordering": ["-count", "name"]},
            bases=(models.Model,),
        )
    ]
