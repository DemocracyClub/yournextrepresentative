# Generated by Django 4.2.8 on 2024-03-06 18:27

import django.db.models.deletion
import sopn_parsing.models
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("sopn_parsing", "0004_awstextractparsedsopn_job_id_and_more"),
    ]

    operations = [
        migrations.CreateModel(
            name="AWSTextractParsedSOPNImage",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "image",
                    models.ImageField(
                        upload_to=sopn_parsing.models.AWSTextractParsedSOPNImage_upload_path
                    ),
                ),
                (
                    "parsed_sopn",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="images",
                        to="sopn_parsing.awstextractparsedsopn",
                    ),
                ),
            ],
        ),
    ]
