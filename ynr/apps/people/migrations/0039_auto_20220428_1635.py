# Generated by Django 3.2.12 on 2022-04-28 15:35

import django.contrib.postgres.indexes
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [("people", "0038_remove_personimage_is_primary")]

    operations = [
        migrations.RemoveIndex(
            model_name="person", name="name_vector_search_index"
        ),
        migrations.AddIndex(
            model_name="person",
            index=django.contrib.postgres.indexes.GinIndex(
                fields=["name_search_vector"], name="name_vector_search_index"
            ),
        ),
    ]