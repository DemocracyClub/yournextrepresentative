# -*- coding: utf-8 -*-
# Generated by Django 1.10.8 on 2018-10-29 15:10
from __future__ import unicode_literals

from django.db import migrations


def move_popolo_person_gfks_to_people_person(apps, schema_editor):
    PeoplePerson = apps.get_model("people", "Person")
    PopoloPerson = apps.get_model("popolo", "Person")
    ContentType = apps.get_model("contenttypes", "ContentType")

    models = [
        apps.get_model("popolo", "Link"),
        apps.get_model("popolo", "OtherName"),
        apps.get_model("popolo", "ContactDetail"),
        apps.get_model("popolo", "Identifier"),
        apps.get_model("popolo", "Source"),
    ]

    people_person_ct = ContentType.objects.get_for_model(PeoplePerson).pk
    popolo_person_ct = ContentType.objects.get_for_model(PopoloPerson).pk

    for model in models:
        model.objects.filter(content_type=popolo_person_ct).update(
            content_type=people_person_ct
        )


class Migration(migrations.Migration):
    dependencies = [("people", "0005_move_person_image_fk_to_person_app")]

    operations = [
        migrations.RunPython(
            move_popolo_person_gfks_to_people_person, migrations.RunPython.noop
        )
    ]
