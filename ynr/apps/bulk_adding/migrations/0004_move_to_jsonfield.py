# -*- coding: utf-8 -*-
# Generated by Django 1.11.20 on 2019-03-14 16:12
from __future__ import unicode_literals

import django.contrib.postgres.fields.jsonb
from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [("bulk_adding", "0003_rawpeople_source_type")]

    operations = [
        migrations.AlterField(
            model_name="rawpeople",
            name="data",
            field=django.contrib.postgres.fields.jsonb.JSONField(),
        )
    ]
