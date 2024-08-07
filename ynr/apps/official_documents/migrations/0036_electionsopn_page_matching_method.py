# Generated by Django 4.2.10 on 2024-04-01 06:39

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("official_documents", "0035_move_officialdocument_to_ballot_sopn"),
    ]

    operations = [
        migrations.AddField(
            model_name="electionsopn",
            name="page_matching_method",
            field=models.CharField(
                choices=[
                    ("Automatically matched", "Auto Matched"),
                    ("Manually matched", "Manual Matched"),
                ],
                max_length=255,
                null=True,
            ),
        ),
    ]
