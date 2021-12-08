import re
from datetime import datetime
from os.path import join
from urllib.parse import urlencode

import dateutil.parser
import magic
import requests
from django.conf import settings
from django.core.management.base import BaseCommand
from django.db import transaction

from candidates.models import PartySet
from popolo.models import Organization

emblem_directory = join(settings.BASE_DIR, "data", "party-emblems")
base_emblem_url = (
    "http://search.electoralcommission.org.uk/Api/Registrations/Emblems/"
)


def find_index(list, predicate):
    for i, e in enumerate(list):
        if predicate(e):
            return i
    return -1


def get_descriptions(party):
    return [
        {"description": d["Description"], "translation": d["Translation"]}
        for d in party["PartyDescriptions"]
    ]


class Command(BaseCommand):
    help = "Update parties from a CSV of party data"

    def handle(self, **options):
        self.mime_type_magic = magic.Magic(mime=True)
        self.gb_parties, _ = PartySet.objects.get_or_create(slug="gb")
        self.ni_parties, _ = PartySet.objects.get_or_create(slug="ni")
        start = 0
        per_page = 30
        url = (
            "http://search.electoralcommission.org.uk/api/search/Registrations"
        )
        params = {
            "rows": per_page,
            "et": ["pp", "ppm"],
            "register": ["gb", "ni", "none"],
            "regStatus": ["registered", "deregistered", "lapsed"],
            "period": [
                "127",
                "135",
                "136",
                "205",
                "207",
                "217",
                "2508",
                "2510",
                "2512",
                "2514",
                "281",
                "289",
                "301",
                "303",
                "305",
                "3560",
                "37",
                "38",
                "4",
                "404",
                "410",
                "445",
                "49",
                "60",
                "62",
                "68",
                "74",
            ],
        }
        with transaction.atomic():
            total = None
            while total is None or start <= total:
                params["start"] = start
                resp = requests.get(
                    url + "?" + urlencode(params, doseq=True)
                ).json()
                if total is None:
                    total = resp["Total"]
                self.parse_data(resp["Result"])
                start += per_page

    def parse_data(self, ec_parties_data):
        for ec_party in ec_parties_data:
            ec_party_id = ec_party["ECRef"].strip()
            # We're only interested in political parties:
            if not ec_party_id.startswith("PP"):
                continue
            party_id = self.clean_id(ec_party_id)
            if ec_party["RegulatedEntityTypeName"] == "Minor Party":
                register = ec_party["RegisterNameMinorParty"].replace(
                    " (minor party)", ""
                )
            else:
                register = ec_party["RegisterName"]
            party_name, party_dissolved = self.clean_name(
                ec_party["RegulatedEntityName"]
            )
            party_founded = self.clean_date(ec_party["ApprovedDate"])
            # Does this party already exist?  If not, create a new one.
            try:
                party = Organization.objects.get(slug=party_id)
                print("Got the existing party:", party.name)
            except Organization.DoesNotExist:
                party = Organization.objects.create(
                    name=party_name, slug=party_id
                )
                print(
                    "Couldn't find {}, creating a new party {}".format(
                        party_id, party_name
                    )
                )

            party.name = party_name
            party.classification = "Party"
            party.founding_date = party_founded
            party.end_date = party_dissolved
            party.register = register
            {
                "Great Britain": self.gb_parties,
                "Northern Ireland": self.ni_parties,
            }[register].parties.add(party)
            party.identifiers.update_or_create(
                scheme="electoral-commission",
                defaults={"identifier": ec_party_id},
            )
            party.other_names.filter(note="registered-description").delete()
            for d in get_descriptions(ec_party):
                value = d["description"]
                translation = d["translation"]
                if translation:
                    value = "{} | {}".format(value, translation)
                party.other_names.create(
                    name=value, note="registered-description"
                )
            party.save()

    def clean_date(self, date):
        timestamp = re.match(r"\/Date\((\d+)\)\/", date).group(1)
        dt = datetime.fromtimestamp(int(timestamp) / 1000.0)
        return dt.strftime("%Y-%m-%d")

    def clean_name(self, name):
        name = name.strip()
        if "de-registered" not in name.lower():
            return name, "9999-12-31"

        match = re.match(r"(.+)\[De-registered ([0-9]+/[0-9]+/[0-9]+)\]", name)
        name, deregistered_date = match.groups()
        name = re.sub(r"\([Dd]e-?registered [^\)]+\)", "", name)
        deregistered_date = dateutil.parser.parse(
            deregistered_date, dayfirst=True
        ).strftime("%Y-%m-%d")

        return name.strip(), deregistered_date

    def clean_id(self, party_id):
        party_id = re.sub(r"^PPm?\s*", "", party_id).strip()
        return "party:{}".format(party_id)
