"""
This data migration takes a CSV* exported from EveryElection
and uses it to match up and change the identifier for each post it finds.

When it's found a post, it makes a new `PostIdentifier` model with
the previous `slug` value, updates the slug and sets other fields like
start and end dates, etc.

* It's actually two files to deal with two cases:

1. The ballot has a post that is a division of an organisation
2. The ballot has a post that's actually an organisation, but where
   we created a pseudo-post for it at import time (for directly elected mayors,
   PCCs, etc)

"""

from django.db import migrations
import csv
import re


def update_or_create_post_identifier(post):
    identifier_label = None

    if post.identifier:
        identifier_value = post.identifier
        if identifier_value.startswith("unit_id"):
            identifier_label = "unit_id"
        if identifier_value.startswith("gla"):
            identifier_label = "legacy_slug"
        if identifier_value.startswith("gss"):
            identifier_label = "gss"
        if identifier_value.startswith("osni_oid"):
            identifier_label = "osni_oid"
        if re.match(r"^[A-Z]{3}", identifier_value.split(":")[0]):
            identifier_label = "dc_slug"
    else:
        if re.match(r"[\d]+", post.slug):
            identifier_label = "mapit_id"
            identifier_value = post.slug
        else:
            identifier_label = "legacy_slug"
            identifier_value = post.slug

    post.postidentifier_set.update_or_create(
        identifier=identifier_value,
        post=post,
        defaults={"label": identifier_label},
    )


def populate_from_ee_divisions(apps, schema_editor):

    Ballot = apps.get_model("candidates", "Ballot")
    Post = apps.get_model("popolo", "Post")
    data_file = open("data/ee_post_identifiers_2020-01.csv")

    for line in csv.DictReader(data_file.readlines()):
        try:
            ballot = Ballot.objects.get(ballot_paper_id=line["election_id"])
        except Ballot.DoesNotExist:
            continue

        existing_post_qs = Post.objects.filter(
            start_date=line["start_date"],
            slug=line["slug"],
            organization__slug="{}:{}".format(
                line["organisation_type"], line["org_slug"]
            ),
        )
        if existing_post_qs.exists():
            post = existing_post_qs.first()
        else:
            post = ballot.post
            post.start_date = line["start_date"]
        post.end_date = line["end_date"]
        post.territory_code = line["territory_code"]
        post.name = line["name"]

        if line["official_identifier"] != post.identifier:
            update_or_create_post_identifier(post)
            post.identifier = line["official_identifier"]
        post.slug = line["slug"]

        post.save()
        ballot.post = post
        ballot.save()


def populate_from_ee_no_divisions(apps, schema_editor):

    Ballot = apps.get_model("candidates", "Ballot")
    Post = apps.get_model("popolo", "Post")
    data_file = open("data/ee_post_identifiers_no_divisions_2020-01.csv")

    for line in csv.DictReader(data_file.readlines()):
        try:
            ballot = Ballot.objects.get(ballot_paper_id=line["election_id"])
        except Ballot.DoesNotExist:
            continue

        existing_post_qs = Post.objects.filter(
            start_date=line["start_date"],
            slug=line["slug"],
            organization__slug="{}:{}".format(
                line["organisation_type"], line["slug"]
            ),
        )
        if existing_post_qs.exists():
            post = existing_post_qs.first()
        else:
            post = ballot.post
            post.start_date = line["start_date"]
        post.end_date = line["end_date"]
        post.territory_code = line["territory_code"]
        post.name = line["name"]

        if line["gss"] != post.identifier:
            update_or_create_post_identifier(post)
            post.identifier = "gss:{}".format(line["gss"])
        post.slug = line["slug"]

        post.save()
        ballot.post = post
        ballot.save()


def clean_up_tmp_ids(apps, schema_editor):
    Post = apps.get_model("popolo", "Post")
    posts = Post.objects.filter(slug__in=["UTW:boaness-and-blackness"])
    posts.update(identifier="gss:S13002936")


class Migration(migrations.Migration):

    dependencies = [("popolo", "0033_unique_on_start_date")]

    operations = [
        migrations.RunPython(
            populate_from_ee_divisions, migrations.RunPython.noop
        ),
        migrations.RunPython(
            populate_from_ee_no_divisions, migrations.RunPython.noop
        ),
        migrations.RunPython(clean_up_tmp_ids, migrations.RunPython.noop),
    ]
