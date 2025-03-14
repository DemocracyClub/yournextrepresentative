# -*- coding: utf-8 -*-
# Generated by Django 1.10.8 on 2018-09-03 12:14
from __future__ import unicode_literals

from django.db import migrations


def add_independent_party(apps, schema_editor):
    Party = apps.get_model("parties", "Party")
    Party.objects.update_or_create(
        ec_id="ynmp-party:2",
        defaults={"name": "Independent", "date_registered": "1832-06-07"},
    )


class Migration(migrations.Migration):
    dependencies = [("parties", "0001_initial")]

    operations = [
        migrations.RunPython(add_independent_party, migrations.RunPython.noop)
    ]
