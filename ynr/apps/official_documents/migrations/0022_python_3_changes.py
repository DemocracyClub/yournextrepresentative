# -*- coding: utf-8 -*-
# Generated by Django 1.10.8 on 2018-10-03 18:31
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("official_documents", "0021_auto_20180406_1555")]

    operations = [
        migrations.AlterField(
            model_name="officialdocument",
            name="document_type",
            field=models.CharField(
                choices=[("Nomination paper", "Nomination paper")],
                max_length=100,
            ),
        )
    ]
