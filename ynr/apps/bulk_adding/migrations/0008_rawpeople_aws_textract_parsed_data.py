# Generated by Django 4.2.6 on 2023-11-21 15:22

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("sopn_parsing", "0002_awstextractparsedsopn"),
        ("bulk_adding", "0007_alter_rawpeople_data"),
    ]

    operations = [
        migrations.AddField(
            model_name="rawpeople",
            name="aws_textract_parsed_data",
            field=models.OneToOneField(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                to="sopn_parsing.awstextractparsedsopn",
            ),
        ),
    ]