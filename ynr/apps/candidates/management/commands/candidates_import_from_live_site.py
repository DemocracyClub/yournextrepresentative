import json
from contextlib import contextmanager

import people.models
import requests
from api.next.serializers import OrganizationSerializer
from candidates.models import Ballot
from django.conf import settings
from django.contrib.auth.models import User
from django.core.files.storage import FileSystemStorage
from django.core.management import call_command
from django.core.management.base import BaseCommand
from parties.api.next.serializers import PartySerializer
from parties.importer import YNRPartyDescriptionImporter
from parties.models import Party
from people.api.next.serializers import (
    PersonIdentifierSerializer,
    PersonSerializer,
)
from people.models import PersonIdentifier
from popolo import models as pmodels
from popolo.api.next.serializers import CandidacyOnPersonSerializer
from popolo.models import Membership


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

    def add_arguments(self, parser):
        parser.add_argument(
            "--site-url",
            help="Base URL for the live site",
            default="https://candidates.democracyclub.org.uk/",
        )
        # parser.add_argument(
        #     "--include-images",
        #     action="store_true",
        #     help="Download Person images when importing",
        # )

    def handle(self, **options):

        self.image_storage = FileSystemStorage()
        self.ynr_url = options["site_url"]
        self.party_cache = {}
        self.ballot_cache = {}
        self.stdout.write(
            "Importing parties from The Electoral Commission (using `parties_import_from_ec`)"
        )
        call_command("parties_import_from_ec", verbosity=options["verbosity"])

        self.stdout.write(
            "Importing elections from {}".format(
                getattr(
                    settings,
                    "EE_BASE_URL",
                    "https://elections.democracyclub.org.uk/",
                )
            )
        )
        call_command(
            "uk_create_elections_from_every_election",
            verbosity=options["verbosity"],
            full=True,
        )

        self.stdout.write("Mirroring {}".format(self.ynr_url))
        self.mirror_from_api(include_images=options.get("include_images"))
        call_command(
            "parties_update_current_candidates", verbosity=options["verbosity"]
        )

    def get_api_results(self, endpoint, api_version="next"):
        if "ballots" in endpoint:
            url = (
                "{base_url}/media/cached-api/latest/ballots-000001.json".format(
                    base_url=self.ynr_url
                )
            )
        elif "people" in endpoint:
            url = (
                "{base_url}/media/cached-api/latest/people-000001.json".format(
                    base_url=self.ynr_url
                )
            )
        else:
            url = "{base_url}api/{api_version}/{endpoint}/?format=json&page_size=200".format(
                base_url=self.ynr_url,
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

    def get_user_from_username(self, username):
        if not username:
            return None
        return User.objects.get_or_create(username=username)[0]

    def get_cached_party(self, party_id):
        if party_id not in self.party_cache:
            try:
                self.party_cache[party_id] = Party.objects.get(ec_id=party_id)
            except Party.DoesNotExist:
                self.party_cache[party_id] = self.import_single_party(party_id)
        return self.party_cache[party_id]

    def get_cached_ballot(self, ballot_paper_id):
        if ballot_paper_id not in self.ballot_cache:
            self.ballot_cache[ballot_paper_id] = Ballot.objects.get(
                ballot_paper_id=ballot_paper_id
            )
        return self.ballot_cache[ballot_paper_id]

    def import_organizations(self):
        for organization_data in self.get_api_results("organizations"):
            with show_data_on_error("organization_data", organization_data):
                slug = organization_data["slug"]
                classification = slug.split(":")[0]
                try:
                    instance = pmodels.Organization.objects.get(
                        slug=slug, classification=classification
                    )
                except pmodels.Organization.DoesNotExist:
                    instance = None

                serializer = OrganizationSerializer(
                    data=organization_data, instance=instance
                )
                if serializer.is_valid():
                    serializer.save()
                else:
                    raise ValueError(serializer.errors)

    def import_party_descriptions(self):
        importer = YNRPartyDescriptionImporter()
        importer.do_import()

    def import_people(self):
        for person_data in self.get_api_results("people"):
            with show_data_on_error("person_data", person_data):
                try:
                    instance = people.models.Person.objects.get(
                        pk=person_data["id"]
                    )
                    instance.tmp_person_identifiers.all().delete()
                except people.models.Person.DoesNotExist:
                    instance = None

                serializer = PersonSerializer(
                    data=person_data, instance=instance
                )
                if serializer.is_valid():
                    person = serializer.save()
                else:
                    raise ValueError(serializer.errors)

                if person_data["other_names"]:
                    for other_name in person_data["other_names"]:
                        person.other_names.create(
                            name=other_name["name"], note=other_name["note"]
                        )
                if person_data["identifiers"]:

                    for identifier in person_data["identifiers"]:
                        if not identifier["value"]:
                            continue
                        serializer = PersonIdentifierSerializer(data=identifier)
                        if serializer.is_valid():
                            serializer.save(person=person)
                        else:
                            raise ValueError(serializer.errors)

                if person_data["candidacies"]:
                    for candidacy in person_data["candidacies"]:
                        ballot_paper_id = candidacy["ballot"]["ballot_paper_id"]
                        if ballot_paper_id.startswith("tmp_"):
                            # Ignore tmp ballots as they should be removed from
                            # YNR anyway
                            continue
                        try:
                            ballot = self.get_cached_ballot(ballot_paper_id)
                        except Ballot.DoesNotExist:
                            ballot = None
                            self.stderr.write(
                                "WARNING: Can't find Ballot {}, skipping".format(
                                    ballot_paper_id
                                )
                            )
                            continue
                        party = self.get_cached_party(
                            candidacy["party"]["ec_id"]
                        )

                        serializer = CandidacyOnPersonSerializer(data=candidacy)
                        if serializer.is_valid():
                            if ballot:
                                person.not_standing.remove(ballot.election)
                                serializer.save(
                                    person=person, ballot=ballot, party=party
                                )
                        else:
                            raise ValueError(serializer.errors)

    def import_single_party(self, party_id):
        """
        The EC site no longer has all parties listed, so we need to get an hoc
        ones from YNR
        """
        url = "{}api/next/parties/{}?format=json".format(self.ynr_url, party_id)
        r = requests.get(url)
        party_json = r.json()
        party_json["status"] = "Deregistered"
        serializer = PartySerializer(data=party_json)
        if serializer.is_valid():
            return serializer.save()
        raise ValueError(serializer.errors)

    def warm_cache(self):
        ballots = Ballot.objects.all()
        for ballot in ballots:
            self.ballot_cache[ballot.ballot_paper_id] = ballot
        parties = Party.objects.all()
        for party in parties:
            self.party_cache[party.ec_id] = party

    def remove_objects_to_be_replaced(self):
        pmodels.OtherName.objects.all().delete()
        Membership.objects.all().delete()
        PersonIdentifier.objects.all().delete()

    def mirror_from_api(self, include_images):
        self.warm_cache()
        self.remove_objects_to_be_replaced()
        self.stdout.write("Importing Organizations")
        self.import_organizations()
        self.stdout.write("Importing People")
        self.import_people()
        self.stdout.write("Importing PartyDescriptions")
        self.import_party_descriptions()

        return
