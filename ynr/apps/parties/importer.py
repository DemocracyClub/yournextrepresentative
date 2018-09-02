import os
from urllib.parse import urlencode, urljoin
import re
from datetime import datetime
from tempfile import NamedTemporaryFile
import mimetypes
import magic
import dateutil.parser

import requests

from .constants import EC_API_BASE, EC_EMBLEM_BASE, DEFAULT_EMBLEMS
from .models import Party, PartyDescription, PartyEmblem


class ECPartyImporter:
    def __init__(self):
        self.collector = []
        self.base_url = EC_API_BASE
        self.per_page = 50
        # Params relating to the search criteria on
        # http://search.electoralcommission.org.uk
        self.params = {
            "rows": self.per_page,
            #  Entity type.
            # Select only 'Political party' (PP) and 'Minor party' (PPm)
            # as other types like 'Referendum participant' or 'Non-party
            # campaigner' can't field candidates
            "et": ["pp", "ppm"],
            # For an unknown reason some parties don't have a register.
            # We assume 'GB' in that case, but need to select them here.
            "register": ["gb", "ni", "none"],
            "regStatus": ["registered", "deregistered", "lapsed"],
            # This is taken directly from the params on the EC's website
            # and are assumed to be a list of the dates or 'reporting periods'
            # the party was active.
            "period": [
                "3560",
                "3568",
                "2514",
                "2508",
                "2510",
                "2512",
                "445",
                "410",
                "404",
                "289",
                "303",
                "305",
                "301",
                "281",
                "217",
                "207",
                "205",
                "136",
                "135",
                "127",
                "74",
                "68",
                "62",
                "60",
                "49",
                "37",
                "38",
                "4",
            ],
        }

    def get_party_list(self, start):
        params = self.params
        params["start"] = start
        url = "{}?{}".format(self.base_url, urlencode(params, doseq=True))
        req = requests.get(url)
        req.raise_for_status()
        return req.json()

    def do_import(self):
        start = 0
        party_list = self.get_party_list(start)
        while start <= int(party_list["Total"]):
            for party_dict in party_list["Result"]:
                party = ECParty(party_dict)
                party_model, created = party.save()
                if created:
                    self.collector.append(party_model)
            start = start + self.per_page
            party_list = self.get_party_list(start)
        return self.collector


class ECParty(dict):
    """
    A python representation of the party JSON from the EC API

    """

    def __init__(self, party_dict):
        self.update(**party_dict)
        self.model = None
        self.created = False
        required_fields = ("RegulatedEntityName", "ECRef", "RegisterName")
        for field in required_fields:
            if not field in self:
                raise ValueError("{} missing".format(field))

    def save(self):
        self.model, self.created = Party.objects.update_or_create(
            ec_id=self.ec_id,
            defaults={
                "name": self.cleaned_name,
                "register": self.register,
                "status": self.registration_status,
                "date_registered": self.parse_date(self["ApprovedDate"]),
                "date_deregistered": self.date_deregistered,
            },
        )

        for description in self.get("PartyDescriptions", []):
            text = " | ".join(
                [
                    d
                    for d in (
                        description["Description"],
                        description.get("Translation", None),
                    )
                    if d
                ]
            )
            PartyDescription.objects.update_or_create(
                description=text,
                party=self.model,
                defaults={
                    "date_description_approved": self.parse_date(
                        description["DateDescriptionFirstApproved"]
                    )
                },
            )

        for emblem_dict in self.get("PartyEmblems", []):
            emblem = ECEmblem(self.model, emblem_dict)
            emblem.save()

        return (self.model, self.created)

    @property
    def ec_id(self):
        return self["ECRef"]

    @property
    def cleaned_name(self):
        name = self["RegulatedEntityName"]

        # Remove [De-registered] tag in name
        # (the date is parsed in `date_deregistered`)
        matcher = re.compile("[\[\(]de(-?)registered .*", flags=re.I)
        name = matcher.split(name)[0].strip()

        # Do some general cleaning
        name = re.sub("\s+", " ", name)
        return name

    @property
    def date_deregistered(self):
        if not self.registration_status == "Deregistered":
            return None

        matcher = re.compile(r"([0-9]+/[0-9]+/[0-9]+)\]")
        deregistered_date = matcher.search(self["RegulatedEntityName"])
        if deregistered_date:
            return dateutil.parser.parse(
                deregistered_date.group(1), dayfirst=True
            )
        else:
            raise ValueError(
                "Unknown deregistrtion date for '{}'".format(
                    self["RegulatedEntityName"]
                )
            )

    @property
    def register(self):
        if not self["RegisterName"] and "PPm" in self.ec_id:
            # Minor parties don't always need to be on a register
            return None
        expected_names = ["Northern Ireland", "Great Britain"]
        if self["RegisterName"] not in expected_names:
            raise ValueError(
                "{} is an unknown register for party {}".format(
                    self["RegisterName"], self.ec_id
                )
            )
        if self["RegisterName"] == "Northern Ireland":
            return "NI"
        else:
            return "GB"

    @property
    def registration_status(self):
        if self["RegistrationStatusName"] not in ["Deregistered", "Registered"]:
            raise ValueError(
                "{} is an unknown registration status".format(
                    self["RegistrationStatusName"]
                )
            )
        return self["RegistrationStatusName"]

    def parse_date(self, date_str):
        timestamp = re.match(r"\/Date\((\d+)\)\/", date_str).group(1)
        dt = datetime.fromtimestamp(int(timestamp) / 1000.)
        return dt.strftime("%Y-%m-%d")


class ECEmblem:
    def __init__(self, party, emblem_dict):
        self.party = party
        self.emblem_dict = emblem_dict

    def download_emblem(self):
        url = "{}/{}".format(EC_EMBLEM_BASE, self.emblem_dict["Id"])
        ntf = NamedTemporaryFile(delete=False)
        r = requests.get(url)
        with open(ntf.name, "wb") as f:
            f.write(r.content)
        return ntf.name

    def save(self):
        existing_emblem = PartyEmblem.objects.filter(
            ec_emblem_id=self.emblem_dict["Id"], party=self.party
        )
        if existing_emblem.exists():
            return (existing_emblem.first(), False)

        image_file_name = self.download_emblem()
        mime_type = magic.Magic(mime=True).from_file(image_file_name)
        extension = mimetypes.guess_extension(mime_type.decode("utf8"))
        if extension == ".html":
            #  Something has gone wrong here, maybe the EC site is down
            # or the file is raising a 404 for some reason.
            # Either way, we don't want this file to be saved
            return
        filename = "Emblem_{}{}".format(self.emblem_dict["Id"], extension)

        emblem = PartyEmblem.objects.create(
            ec_emblem_id=self.emblem_dict["Id"],
            party=self.party,
            description=self.emblem_dict["MonochromeDescription"],
            default=self.get_default(),
        )

        emblem.image.save(filename, open(image_file_name, "rb"))
        os.remove(image_file_name)
        return (emblem, True)

    def get_default(self):
        return (
            DEFAULT_EMBLEMS.get(self.party.ec_id, False)
            == self.emblem_dict["Id"]
        )
