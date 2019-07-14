from contextlib import contextmanager
import errno
import hashlib
import json
from os import makedirs
from os.path import dirname, exists, join
import re
import shutil

from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType
from django.core.files.storage import FileSystemStorage
from django.core.management.base import BaseCommand, CommandError
from django.core.management import call_command
from django.core.management.color import no_style
from django.db import connection, transaction
from django.utils.six import string_types
from django.utils.six.moves.urllib_parse import urlsplit, urlunsplit

import requests

import people.models
from candidates import models
from elections import models as emodels
from popolo import models as pmodels
from people.models import PersonImage, PersonIdentifier
from parties.models import Party

from ..images import get_image_extension

CACHE_DIRECTORY = join(dirname(__file__), ".download-cache")

# n.b. There is some repeated code between here and
# candidates/migrations/0009_migrate_to_django_popolo.py, but we want
# to keep the code in the migration frozen, and factoring it out would
# risk people making changes that broke the migration.


@contextmanager
def show_data_on_error(variable_name, data):
    """A context manager to output problematic data on any exception

    If there's an error when importing a particular person, say, it's
    useful to have in the error output that particular structure that
    caused problems. If you wrap the code that processes some data
    structure (a dictionary called 'my_data', say) with this:

        with show_data_on_error('my_data', my_data'):
            ...
            process(my_data)
            ...

    ... then if any exception is thrown in the 'with' block you'll see
    the data that was being processed when it was thrown."""

    try:
        yield
    except:
        message = "An exception was thrown while processing {0}:"
        print(message.format(variable_name))
        print(json.dumps(data, indent=4, sort_keys=True))
        raise


class Command(BaseCommand):
    help = "Import all data from a live YNR site"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.image_storage = FileSystemStorage()

    def add_arguments(self, parser):
        parser.add_argument("SITE-URL", help="Base URL for the live site")
        parser.add_argument(
            "--ignore-images",
            action="store_true",
            help="Don't download images when importing",
        )

    def check_database_is_empty(self):
        non_empty_models = []
        for model_class in (
            # Base Popolo models that YNR uses:
            people.models.Person,
            pmodels.Membership,
            pmodels.Organization,
            pmodels.Post,
            pmodels.ContactDetail,
            pmodels.OtherName,
            pmodels.Identifier,
            pmodels.Link,
            # Additional models:
            models.PartySet,
            models.LoggedAction,
            models.PersonRedirect,
            emodels.Election,
        ):
            if model_class.objects.exists():
                non_empty_models.append(model_class)
        if non_empty_models:
            print("There were already objects of these models:")
            for model_class in non_empty_models:
                print(" ", model_class)
            msg = "This command should only be run on an empty database"
            raise CommandError(msg)

    def get_api_results(self, endpoint, api_version="v0.9"):
        page = 1

        if "posts" in endpoint:
            url = "{base_url}/media/cached-api/latest/posts-000001.json".format(
                base_url=self.base_url
            )
        elif "persons" in endpoint:
            url = "{base_url}/media/cached-api/latest/persons-000001.json".format(
                base_url=self.base_url
            )
        else:
            url = "{base_url}{api_version}/{endpoint}/?format=json&page_size=200".format(
                base_url=self.base_api_url,
                api_version=api_version,
                endpoint=endpoint,
            )

        while url:
            self.stdout.write("Fetching " + url)
            r = requests.get(url)
            data = r.json()
            for result in data["results"]:
                yield (result)
            url = data.get("next")

    def add_related(self, o, model_class, related_data_list):
        for related_data in related_data_list:
            with show_data_on_error("related_data", related_data):
                model_class.objects.create(content_object=o, **related_data)

    def get_user_from_username(self, username):
        if not username:
            return None
        return User.objects.get_or_create(username=username)[0]

    def get_url_cached(self, url):
        try:
            makedirs(CACHE_DIRECTORY)
        except OSError as e:
            if e.errno != errno.EEXIST:
                raise
        filename = join(
            CACHE_DIRECTORY, hashlib.md5(url.encode("utf8")).hexdigest()
        )
        if exists(filename):
            return filename
        else:
            print("\nDownloading {} ...".format(url))
            with open(filename, "wb") as f:
                r = requests.get(url, stream=True)
                r.raise_for_status()
                r.raw.decode_content = True
                shutil.copyfileobj(r.raw, f)
            print("done")
        return filename

    def mirror_from_api(self, ignore_images):
        party_sets_by_slug = {}
        for party_set_data in self.get_api_results("party_sets"):
            with show_data_on_error("party_set_data", party_set_data):
                del party_set_data["url"]
                party_set, _ = models.PartySet.objects.update_or_create(
                    **party_set_data
                )
                party_sets_by_slug[party_set.slug] = party_set

        # Parties
        for party_dict in self.get_api_results("parties", "next"):
            # Only import a small subset of party data needed to get
            # memberships working. The canonical source of parties is The
            # Electoral Commission so the EC importer in the parties app should
            # be used to get the full party info.
            Party.objects.update_or_create(
                ec_id=party_dict["ec_id"],
                defaults={
                    "name": party_dict["name"],
                    "register": party_dict["register"],
                    "date_registered": party_dict["date_registered"],
                    "legacy_slug": party_dict["legacy_slug"],
                },
            )

        organization_to_parent = {}
        for organization_data in self.get_api_results("organizations"):
            if organization_data["classification"] == "Party":
                # We don't use this model for party data any more, so this data
                # isn't needed
                continue
            with show_data_on_error("organization_data", organization_data):
                kwargs = dict(
                    name=organization_data["name"],
                    classification=organization_data["classification"],
                    founding_date=organization_data["founding_date"],
                    dissolution_date=organization_data["dissolution_date"],
                    slug=organization_data["id"],
                    register=organization_data["register"],
                )
                if pmodels.Organization.objects.filter(**kwargs).count() > 1:
                    # Because there are no unique constraints on Organization,
                    # the below update_or_create can fail on
                    # MultipleObjectsReturned in some cases.
                    # If that will happen, assuming everything is created
                    # already and skip this org.
                    continue
                o, _ = pmodels.Organization.objects.update_or_create(**kwargs)

                self.add_related(
                    o, pmodels.Identifier, organization_data["identifiers"]
                )
                self.add_related(
                    o,
                    pmodels.ContactDetail,
                    organization_data["contact_details"],
                )
                self.add_related(
                    o, pmodels.OtherName, organization_data["other_names"]
                )
                self.add_related(o, pmodels.Link, organization_data["links"])
                self.add_related(
                    o, pmodels.Source, organization_data["sources"]
                )
                # Save any parent:
                if organization_data["parent"]:
                    organization_to_parent[
                        organization_data["id"]
                    ] = organization_data["parent"]["id"]
        # Set any parent organizations:
        for child_slug, parent_slug in organization_to_parent.items():
            child = pmodels.Organization.objects.get(slug=child_slug)
            parent = pmodels.Organization.objects.get(slug=parent_slug)
            child.parent = parent
            child.save()

        for election_data in self.get_api_results("elections"):
            with show_data_on_error("election_data", election_data):
                kwargs = {
                    k: election_data[k]
                    for k in (
                        "name",
                        "winner_membership_role",
                        "candidate_membership_role",
                        "election_date",
                        "for_post_role",
                        "current",
                        "use_for_candidate_suggestions",
                        "party_lists_in_use",
                        "default_party_list_members_to_show",
                        "show_official_documents",
                        "ocd_division",
                        "description",
                    )
                }
                e, _ = emodels.Election.objects.update_or_create(
                    slug=election_data["id"], defaults=kwargs
                )
                election_org = election_data.get("organization")
                if election_org:
                    e.organization = pmodels.Organization.objects.get(
                        slug=election_org["id"]
                    )
                e.save()

        for post_data in self.get_api_results("posts"):
            with show_data_on_error("post_data", post_data):
                post = pmodels.Post(
                    label=post_data["label"],
                    role=post_data["role"],
                    slug=post_data["id"],
                    group=post_data["group"],
                )
                post.organization = pmodels.Organization.objects.get(
                    slug=post_data["organization"]["id"]
                )

                post.save()

                if post_data.get("party_set"):
                    party_set_data = post_data["party_set"]
                    post.party_set = models.PartySet.objects.get(
                        pk=party_set_data["id"]
                    )
                    post.save()
                for election_data in post_data["elections"]:
                    election = emodels.Election.objects.get(
                        slug=election_data["id"]
                    )
                    models.Ballot.objects.update_or_create(
                        post=post,
                        election=election,
                        candidates_locked=election_data["candidates_locked"],
                        ballot_paper_id=election_data["ballot_paper_id"],
                    )
        person_to_image_data = {}
        for person_data in self.get_api_results("persons"):
            with show_data_on_error("person_data", person_data):
                kwargs = {
                    k: person_data[k]
                    for k in (
                        "id",
                        "name",
                        "honorific_prefix",
                        "honorific_suffix",
                        "sort_name",
                        "email",
                        "gender",
                        "birth_date",
                        "death_date",
                    )
                }
                kwargs["versions"] = json.dumps(person_data["versions"])
                person = people.models.Person.objects.create(**kwargs)
                if not ignore_images:
                    person_to_image_data[person] = person_data["images"]

                value_types = [
                    v[0] for v in PersonIdentifier.objects.select_choices()
                ]
                for value_type in value_types:
                    if value_type in person_data and person_data[value_type]:
                        PersonIdentifier.objects.update_or_create(
                            person=person,
                            value_type=value_type,
                            value=person_data[value_type],
                        )

                self.add_related(
                    person, pmodels.OtherName, person_data["other_names"]
                )
                self.add_related(person, pmodels.Link, person_data["links"])

        for m_data in self.get_api_results("memberships", "next"):
            with show_data_on_error("m_data", m_data):
                kwargs = {
                    k: m_data[k]
                    for k in ("label", "role", "start_date", "end_date")
                }
                try:
                    kwargs["person"] = people.models.Person.objects.get(
                        pk=m_data["person"]["id"]
                    )
                except people.models.Person.DoesNotExist:
                    # Chances are this person was created since the last
                    # cached person run was updated. It's ok to ignore this
                    continue
                if m_data.get("party"):
                    kwargs["party"] = Party.objects.get(
                        ec_id=m_data["party"]["ec_id"]
                    )
                if m_data.get("organization"):
                    kwargs["organization"] = pmodels.Organization.objects.get(
                        slug=m_data["organization"]["id"]
                    )
                if m_data.get("post"):
                    kwargs["post"] = pmodels.Post.objects.get(
                        slug=m_data["post"]["id"]
                    )
                kwargs["post_election"] = models.Ballot.objects.get(
                    post=kwargs["post"],
                    election=emodels.Election.objects.get(
                        slug=m_data["election"]["id"]
                    ),
                )
                m = pmodels.Membership.objects.create(**kwargs)
                kwargs = {
                    "base": m,
                    "elected": m_data["elected"],
                    "party_list_position": m_data["party_list_position"],
                }
                if m_data.get("election"):
                    kwargs["election"] = emodels.Election.objects.get(
                        slug=m_data["election"]["id"]
                    )
        if not ignore_images:
            for person, image_data_list in person_to_image_data.items():
                for image_data in image_data_list:
                    with show_data_on_error("image_data", image_data):
                        suggested_filename = re.search(
                            r"/([^/]+)$", image_data["image_url"]
                        ).group(1)
                        image_filename = self.get_url_cached(
                            image_data["image_url"]
                        )
                        extension = get_image_extension(image_filename)
                        if not extension:
                            continue
                        PersonImage.objects.update_or_create_from_file(
                            image_filename,
                            join("images", suggested_filename),
                            person,
                            defaults={
                                "md5sum": image_data["md5sum"],
                                "uploading_user": self.get_user_from_username(
                                    image_data.get("uploading_user")
                                ),
                                "copyright": image_data["copyright"] or "",
                                "notes": image_data["notes"] or "",
                                "user_copyright": image_data["user_copyright"]
                                or "",
                                "user_notes": image_data["user_notes"] or "",
                                "source": image_data["source"] or "",
                                "is_primary": image_data["is_primary"],
                            },
                        )
        reset_sql_list = connection.ops.sequence_reset_sql(
            no_style(),
            [
                models.PartySet,
                emodels.Election,
                PersonImage,
                people.models.Person,
            ],
        )
        if reset_sql_list:
            cursor = connection.cursor()
            for reset_sql in reset_sql_list:
                cursor.execute(reset_sql)

    def handle(self, **options):
        with transaction.atomic():
            split_url = urlsplit(options["SITE-URL"])
            if (
                split_url.path not in ("", "/")
                or split_url.query
                or split_url.fragment
            ):
                raise CommandError(
                    "You must only supply the base URL of the site"
                )
            # Then form the base API URL:
            new_url_parts = list(split_url)
            new_url_parts[2] = ""
            self.base_url = urlunsplit(new_url_parts)
            new_url_parts[2] = "/api/"
            self.base_api_url = urlunsplit(new_url_parts)
            self.check_database_is_empty()
            self.mirror_from_api(ignore_images=options["ignore_images"])
            call_command("parties_update_current_candidates")
