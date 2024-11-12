import mimetypes
import os
import re
from datetime import datetime
from tempfile import NamedTemporaryFile
from typing import Dict
from urllib.parse import urlencode

import dateutil.parser
import httpx
import magic
import requests
from candidates.models.popolo_extra import UnsafeToDelete
from django.contrib.admin.utils import NestedObjects
from django.db import connection
from PIL import Image

from .constants import (
    CORRECTED_DESCRIPTION_DATES,
    CORRECTED_PARTY_NAMES_IN_DESC,
    DEFAULT_EMBLEMS,
    EC_API_BASE,
    EC_EMBLEM_BASE,
    JOINT_DESCRIPTION_REGEX,
)
from .models import Party, PartyDescription, PartyEmblem


def make_slug(party_id):
    if "-party:" in party_id:
        return party_id
    prefix = "minor-party" if "PPm" in party_id else "party"

    party_id = re.sub(r"^PPm?\s*", "", party_id).strip()
    return "{}:{}".format(prefix, party_id)


def extract_number_from_id(party_id):
    m = re.search(r"\d+", party_id)
    if m:
        return int(m.group(0), 10)
    return None


def make_joint_party_id(id1, id2):
    numbers = sorted(map(extract_number_from_id, [id1, id2]))
    return "joint-party:{}-{}".format(*numbers)


def make_description_text(ec_description: Dict) -> str:
    """
    Create text for `PartyDescription.description` field from EC-shaped description object
    :return: string
    """
    text = " | ".join(
        [
            d
            for d in (
                ec_description["Description"],
                ec_description.get("Translation"),
            )
            if d
        ]
    )

    # replace en-dash with minus
    return text.replace("\u2013", "\u002d")


class ECPartyImporter:
    def __init__(self):
        self.collector = []
        self.error_collector = []
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
        client = httpx.Client()
        req = client.get(url, timeout=300, follow_redirects=True)
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

    def create_joint_parties(self, raise_on_error=True):
        """
        We create joint parties if one party's description matches the
        JOINT_DESCRIPTION_REGEX (e.g. contains "joint description").

        The new party gets an ID made up of both parties IDs like

        `joint-party:51-83`

        Where each number is the ID of the 'parent' party.

        The lower number ID is always first.

        After successfully creating the joint party, delete the
        PartyDescription related to the individual parties, to make
        sure the joint party is always used.

        """

        qs = PartyDescription.objects.filter(
            description__iregex=JOINT_DESCRIPTION_REGEX
        )

        for description in qs:
            joint_party_name, other_party_names = re.match(
                JOINT_DESCRIPTION_REGEX, description.description, re.IGNORECASE
            ).groups()

            sub_parties = other_party_names.split(", and ")
            for other_party_name in sub_parties:
                # Try to get a corrected name for the other party
                other_party_name = other_party_name.replace("’", "'")
                other_party_name = CORRECTED_PARTY_NAMES_IN_DESC.get(
                    other_party_name, other_party_name
                )
                date = CORRECTED_DESCRIPTION_DATES.get(
                    description.description,
                    description.date_description_approved,
                )

                try:
                    other_party = (
                        Party.objects.filter(
                            name=other_party_name,
                            register=description.party.register,
                        )
                        .active_for_date(date)
                        .get()
                    )
                except Party.DoesNotExist:
                    message = "Can't find: {}".format(other_party_name)
                    if raise_on_error:
                        raise ValueError(message)
                    self.error_collector.append(message)
                    continue
                joint_id = make_joint_party_id(
                    description.party.ec_id, other_party.ec_id
                )
                joint_party, created = Party.objects.update_or_create(
                    ec_id=joint_id,
                    defaults={
                        "name": joint_party_name,
                        "status": "Registered",
                        "register": "GB",
                        "date_registered": description.date_description_approved,
                        "legacy_slug": make_slug(joint_id),
                    },
                )
                if created:
                    self.collector.append(joint_party)

            # check the description is safe to delete
            nested_objects = NestedObjects(using=connection.cursor().db.alias)
            nested_objects.collect([description])
            if len(nested_objects.nested()) > 1:
                raise UnsafeToDelete(
                    f"Can't delete election {description} with related objects"
                )

            description.delete()


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
            if field not in self:
                raise ValueError("{} missing".format(field))

    def save(self):
        self.model, self.created = Party.objects.update_or_create(
            ec_id=self.ec_id,
            defaults={
                "name": self.cleaned_name,
                "alternative_name": self.alternative_name,
                "register": self.register,
                "status": self.registration_status,
                "date_registered": self.parse_date(self["ApprovedDate"]),
                "date_deregistered": self.date_deregistered,
                "legacy_slug": make_slug(self.ec_id),
                "ec_data": self,
                "nations": self.nation_list,
            },
        )

        if self.registration_status == "Registered":
            self.mark_inactive_descriptions()
            self.mark_inactive_emblems()

        for description in self.get("PartyDescriptions", []):
            text = make_description_text(description)
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
        matcher = re.compile(r"[\[\(]de(-?)registered .*", flags=re.I)
        name = matcher.split(name)[0].strip()

        # Do some general cleaning
        name = re.sub(r"\s+", " ", name)
        # replace dash with hyphen
        return name.replace("\u2013", "\u002d")

    @property
    def date_deregistered(self):
        if self.registration_status != "Deregistered":
            return None

        matcher = re.compile(r"([0-9]+/[0-9]+/[0-9]+)\]")
        deregistered_date = matcher.search(self["RegulatedEntityName"])
        if deregistered_date:
            return dateutil.parser.parse(
                deregistered_date.group(1), dayfirst=True
            )
        raise ValueError(
            "Unknown deregistrtion date for '{}'".format(
                self["RegulatedEntityName"]
            )
        )

    @property
    def register(self):
        if not self["RegisterName"] and "PPm" in self.ec_id:
            # Minor parties don't always need to be on a register
            # but for our use let's define them as in GB
            return "GB"
        expected_names = ["Northern Ireland", "Great Britain"]
        if self["RegisterName"] not in expected_names:
            raise ValueError(
                "{} is an unknown register for party {}".format(
                    self["RegisterName"], self.ec_id
                )
            )
        if self["RegisterName"] == "Northern Ireland":
            return "NI"
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

    @property
    def alternative_name(self):
        return self["RegulatedEntityAlternateName"]

    def parse_date(self, date_str):
        timestamp = re.match(r"\/Date\((\d+)\)\/", date_str).group(1)
        dt = datetime.fromtimestamp(int(timestamp) / 1000.0)
        return dt.strftime("%Y-%m-%d")

    @property
    def nation_list(self):
        """
        Generate data for the `nations` field on the party.
        For GB parties, return a list of nation codes where candidates are fielded.
        For NI parties, return None.
        """

        if self.register == "NI":
            return None

        nation_list = []

        if self["FieldingCandidatesInEngland"]:
            nation_list.append("ENG")

        if self["FieldingCandidatesInScotland"]:
            nation_list.append("SCO")

        if self["FieldingCandidatesInWales"]:
            nation_list.append("WAL")

        return nation_list

    def mark_inactive_emblems(self):
        ec_emblem_id_list = [
            emblem["Id"] for emblem in self.get("PartyEmblems", [])
        ]
        inactive_emblems = (
            PartyEmblem.objects.exclude(ec_emblem_id__in=ec_emblem_id_list)
            .filter(party_id=self.model.id)
            .all()
        )

        for emblem in inactive_emblems:
            if emblem.active is not False:
                emblem.active = False
                emblem.save()

    def mark_inactive_descriptions(self):
        ec_description_list = []

        for description in self.get("PartyDescriptions", []):
            ec_description_list.append(make_description_text(description))

        inactive_descriptions = (
            PartyDescription.objects.exclude(
                description__in=ec_description_list
            )
            .filter(party_id=self.model.id)
            .all()
        )

        PartyDescription.objects.filter(party_id=self.model.id).all()

        for description in inactive_descriptions:
            if description.active is not False:
                description.active = False
                description.save()


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

    def clean_image(self, image_file_name):
        # Normalize the image: Sometimes the EC publishes png images with an
        # alpha channel. This breaks later conversion to JPEG.
        # See: https://github.com/jazzband/sorl-thumbnail/issues/564
        with Image.open(image_file_name) as img:
            # Convert RGBA to RGB
            if img.mode == "RGBA":
                # Create a white background and paste the image onto it
                background = Image.new("RGB", img.size, (255, 255, 255))
                background.paste(img, mask=img.split()[3])
                img = background
            # LA is luminance + alpha. e.g. greyscale with transparency
            if img.mode == "LA":
                img = img.convert("L")
            # Save the image as a PNG without alpha
            png_tempfile = NamedTemporaryFile(delete=False, suffix=".png")
            img.save(png_tempfile.name, "PNG")

        return png_tempfile.name

    def save(self):
        existing_emblem = PartyEmblem.objects.filter(
            ec_emblem_id=self.emblem_dict["Id"], party=self.party
        )

        if existing_emblem.exists():
            emblem = existing_emblem.first()
            if emblem.default != self.get_default():
                # Update the default flag in case it's been changed in
                # DEFAULT_EMBLEMS
                emblem.default = self.get_default()
                emblem.save()

            return (emblem, False)

        image_file_name = self.download_emblem()
        mime_type = magic.Magic(mime=True).from_file(image_file_name)
        if not mime_type.startswith("image/"):
            # This isn't an image, so let's not try to save it
            return None
        cleaned_image_file_name = self.clean_image(image_file_name)
        extension = mimetypes.guess_extension(mime_type)
        filename = "Emblem_{}{}".format(self.emblem_dict["Id"], extension)

        emblem, _ = PartyEmblem.objects.update_or_create(
            ec_emblem_id=self.emblem_dict["Id"],
            defaults={
                "party": self.party,
                "description": self.emblem_dict["MonochromeDescription"],
                "default": self.get_default(),
            },
        )

        with open(cleaned_image_file_name, "rb") as f:
            emblem.image.save(filename, f)
        os.remove(image_file_name)
        os.remove(cleaned_image_file_name)
        return (emblem, True)

    def get_default(self):
        return (
            DEFAULT_EMBLEMS.get(self.party.ec_id, False)
            == self.emblem_dict["Id"]
        )


class YNRPartyDescriptionImporter:
    """
    Import all PartyDescription objects from the YNR live site. This will create
    older PartyDescription's that have been removed from the Electoral
    Commission.
    """

    def do_import(self):
        url = "https://candidates.democracyclub.org.uk/api/next/parties/?format=json&page_size=200"
        while url:
            print(f"Fetching {url}")
            r = requests.get(url)
            data = r.json()
            for result in data["results"]:
                self.create_party_description(party_data=result)
            url = data.get("next")

    def create_party_description(self, party_data):
        try:
            party = Party.objects.get(ec_id=party_data["ec_id"])
        except Party.DoesNotExist:
            return print(
                f"Couldn't find party with {party_data['ec_id']}, skipping"
            )

        for description in party_data["descriptions"]:
            (
                party_description_obj,
                created,
            ) = PartyDescription.objects.get_or_create(
                description=description["description"],
                date_description_approved=description[
                    "date_description_approved"
                ],
                party=party,
            )
            if created:
                print(
                    f"Created PartyDescription {party_description_obj.pk}: {party_description_obj.description}"
                )
        return None
