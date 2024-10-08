# Generated by Django 4.2.10 on 2024-04-02 16:09

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("elections", "0020_alter_election_modified"),
        (
            "candidates",
            "0085_alter_personredirect_options_personredirect_created_and_more",
        ),
    ]

    operations = [
        migrations.AddField(
            model_name="loggedaction",
            name="election",
            field=models.ForeignKey(
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                to="elections.election",
            ),
        ),
    ]
