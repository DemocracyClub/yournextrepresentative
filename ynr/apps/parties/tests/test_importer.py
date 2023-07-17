"""
Test some of the basic model use cases

"""
from io import StringIO
from tempfile import NamedTemporaryFile

from django.core.files.storage import DefaultStorage
from django.test import TestCase
from mock import patch

from candidates.tests.helpers import TmpMediaRootMixin
from moderation_queue.tests.paths import (
    BROKEN_IMAGE_FILENAME,
    EXAMPLE_IMAGE_FILENAME,
)
from parties.importer import ECParty, ECPartyImporter, make_description_text
from parties.management.commands.parties_import_from_ec import Command
from parties.models import Party, PartyDescription, PartyEmblem
from parties.tests.fixtures import DefaultPartyFixtures

from .factories import PartyDescriptionFactory, PartyFactory, PartyEmblemFactory

FAKE_PARTY_DICT = {
    "RegulatedEntityName": "Wombles Alliance",
    "RegulatedEntityAlternateName": "Cynghrair Wombles",
    "ECRef": "PP01",
    "RegisterName": "Great Britain",
    "RegistrationStatusName": "Registered",
    "FieldingCandidatesInEngland": True,
    "FieldingCandidatesInScotland": True,
    "FieldingCandidatesInWales": True,
    "ApprovedDate": "/Date(1134345600000)/",
    "PartyDescriptions": [
        {
            "Description": "Make Good Use of Bad Rubbish",
            "Translation": "Gwneud Defnydd Da o Sbwriel Gwael",
            "DateDescriptionFirstApproved": "/Date(1225756800000)/",
        }
    ],
    "PartyEmblems": [
        {
            "PartyEmblemId": 382,
            "MonochromeDescription": "Box containing the word",
            "Id": 382,
        }
    ],
}

FAKE_RESULTS_DICT = {"Total": 1, "Result": [FAKE_PARTY_DICT]}


def make_tmp_file_from_source(source):
    """
    Copy a file to a tmp location, so we can test deleting it without
    deleting the checked in source file.
    """
    with open(source, "rb") as source_file:
        ntf = NamedTemporaryFile(delete=False)
        with open(ntf.name, "wb") as f:
            f.write(source_file.read())
            return ntf.name


class TestECPartyImporter(DefaultPartyFixtures, TmpMediaRootMixin, TestCase):
    def setUp(self):
        super().setUp()
        self.storage = DefaultStorage()

    @patch("parties.importer.ECPartyImporter.get_party_list")
    @patch("parties.importer.ECEmblem.download_emblem")
    def test_importer(self, FakeEmblemPath, FakeGetPartyList):
        FakeGetPartyList.return_value = FAKE_RESULTS_DICT
        FakeEmblemPath.return_value = make_tmp_file_from_source(
            EXAMPLE_IMAGE_FILENAME
        )
        importer = ECPartyImporter()
        new_parties = importer.do_import()
        self.assertEqual(Party.objects.count(), 3)
        self.assertEqual(new_parties[0].name, "Wombles Alliance")

    @patch("parties.importer.ECPartyImporter.get_party_list")
    @patch("parties.importer.ECEmblem.download_emblem")
    def test_import_management_command(self, FakeEmblemPath, FakeGetPartyList):
        FakeGetPartyList.return_value = FAKE_RESULTS_DICT
        FakeEmblemPath.side_effect = [
            make_tmp_file_from_source(EXAMPLE_IMAGE_FILENAME)
        ]
        cmd = Command()

        out = StringIO()
        cmd.stdout = out
        cmd.handle(
            **{
                "clear_emblems": True,
                "skip_create_joint": False,
                "post_to_slack": False,
                "quiet": False,
                "no_color": True,
            }
        )
        self.assertTrue(
            "Found 1 new political parties!" in cmd.stdout.getvalue()
        )

    def test_cleaned_name(self):
        # All actual examples with their expected cleaned name
        cleaning_expected = (
            (
                "Oxfordshire Independent Party [De-registered 03/11/16]",
                "Oxfordshire Independent Party",
            ),
            (
                "British        Unicorn Party (de-registered 2008) [De-registered 04/07/08]",
                "British Unicorn Party",
            ),
            (
                "Communities  United Party (deregistered 27/01/2010) [De-registered 27/01/10]",
                "Communities United Party",
            ),
        )

        for ec_name, cleaned_name in cleaning_expected:
            party = ECParty(
                {
                    "ECRef": "PP01",
                    "RegulatedEntityName": ec_name,
                    "RegisterName": "Great Britain",
                }
            )
            self.assertEqual(party.cleaned_name, cleaned_name)

    def test_nations(self):
        party = ECParty(
            {
                "ECRef": "PP01",
                "RegulatedEntityName": "The S-Club Party",
                "RegisterName": "Northern Ireland",
                "FieldingCandidatesInEngland": False,
                "FieldingCandidatesInWales": False,
                "FieldingCandidatesInScotland": False,
            }
        )

        # Northern Ireland
        self.assertEqual(party.nation_list, None)

        # Great Britain
        party["RegisterName"] = "Great Britain"
        # England Only
        party["FieldingCandidatesInEngland"] = True
        self.assertEqual(party.nation_list, ["ENG"])

        # England and Wales
        party["FieldingCandidatesInWales"] = True
        self.assertEqual(party.nation_list, ["ENG", "WAL"])

        # England, Wales and Scotland
        party["FieldingCandidatesInScotland"] = True
        self.assertEqual(party.nation_list, ["ENG", "SCO", "WAL"])

    def test_make_description_text(self):
        description_only_plus_en_dash = {
            "Description": "Minuses for all - no en–dashes!",
            "Translation": None,
        }

        description_with_translation = {
            "Description": "Oh Well",
            "Translation": "Helaas Pindakaas",
        }

        # a little hard to see, but this tests character conversion from en-dash (U2013) to minus (U002D)
        self.assertEqual(
            make_description_text(description_only_plus_en_dash),
            "Minuses for all - no en-dashes!",
        )
        self.assertEqual(
            make_description_text(description_with_translation),
            "Oh Well | Helaas Pindakaas",
        )

    @patch("parties.importer.ECEmblem.download_emblem")
    def test_save(self, FakeEmblemPath):
        FakeEmblemPath.return_value = make_tmp_file_from_source(
            EXAMPLE_IMAGE_FILENAME
        )
        self.assertEqual(Party.objects.count(), 2)
        self.assertEqual(PartyDescription.objects.count(), 2)
        self.assertFalse(PartyEmblem.objects.all().exists())
        party = ECParty(FAKE_PARTY_DICT)
        party.save()
        self.assertEqual(Party.objects.count(), 3)
        party_model = Party.objects.get(ec_id="PP01")
        self.assertEqual(party_model.name, "Wombles Alliance")
        self.assertEqual(party_model.register, "GB")
        self.assertEqual(party_model.status, "Registered")
        self.assertEqual(
            party_model.descriptions.first().description,
            "Make Good Use of Bad Rubbish | Gwneud Defnydd Da o Sbwriel Gwael",
        )
        self.assertEqual(party_model.emblems.count(), 1)
        self.assertEqual(
            party_model.default_emblem.description, "Box containing the word"
        )

    @patch("parties.importer.ECEmblem.download_emblem")
    def test_emblem_marked_inactive(self, FakeEmblemPath):
        FakeEmblemPath.return_value = make_tmp_file_from_source(
            EXAMPLE_IMAGE_FILENAME
        )
        party = ECParty(FAKE_PARTY_DICT)
        model, created = party.save()
        PartyEmblemFactory(
            party=model,
            ec_emblem_id=861,
            image=EXAMPLE_IMAGE_FILENAME,
            description="test",
            default=False,
        )
        party.mark_inactive_emblems()

        active_emblems = PartyEmblem.objects.filter(
            active=True, party_id=model.id
        ).all()
        self.assertEqual(len(active_emblems), 1)
        self.assertEqual(
            active_emblems[0].ec_emblem_id,
            FAKE_PARTY_DICT["PartyEmblems"][0]["Id"],
        )

        inactive_emblems = PartyEmblem.objects.filter(
            active=False, party_id=model.id
        ).all()
        self.assertEqual(len(inactive_emblems), 1)
        self.assertEqual(inactive_emblems[0].ec_emblem_id, 861)

    @patch("parties.importer.ECEmblem.download_emblem")
    def test_description_marked_inactive(self, FakeEmblemPath):
        FakeEmblemPath.return_value = make_tmp_file_from_source(
            EXAMPLE_IMAGE_FILENAME
        )
        party = ECParty(FAKE_PARTY_DICT)
        model, created = party.save()
        PartyDescriptionFactory(
            party=model,
            description="Inactive",
            date_description_approved="2021-11-22",
        )
        party.mark_inactive_descriptions()

        active_descriptions = PartyDescription.objects.filter(
            active=True, party_id=model.id
        ).all()
        self.assertEqual(len(active_descriptions), 1)
        self.assertEqual(
            active_descriptions[0].description,
            make_description_text(FAKE_PARTY_DICT["PartyDescriptions"][0]),
        )

        inactive_descriptions = PartyDescription.objects.filter(
            active=False, party_id=model.id
        ).all()
        self.assertEqual(len(inactive_descriptions), 1)
        self.assertEqual(inactive_descriptions[0].description, "Inactive")

    @patch("parties.importer.ECEmblem.download_emblem")
    def test_save_with_non_image_emblem(self, FakeEmblemPath):
        FakeEmblemPath.return_value = make_tmp_file_from_source(
            BROKEN_IMAGE_FILENAME
        )
        self.assertFalse(PartyEmblem.objects.all().exists())
        party = ECParty(FAKE_PARTY_DICT)
        party.save()
        self.assertFalse(PartyEmblem.objects.all().exists())

    def test_raises_on_bad_dict(self):
        with self.assertRaises(ValueError):
            ECParty({})

    @patch("parties.importer.ECPartyImporter.get_party_list")
    @patch("parties.importer.ECEmblem.download_emblem")
    @patch.dict("parties.importer.DEFAULT_EMBLEMS", {"PP01": 1}, clear=True)
    def test_set_emblem_default(self, FakeEmblemPath, FakeGetPartyList):
        FakeEmblemPath.side_effect = [
            make_tmp_file_from_source(EXAMPLE_IMAGE_FILENAME),
            make_tmp_file_from_source(EXAMPLE_IMAGE_FILENAME),
            make_tmp_file_from_source(EXAMPLE_IMAGE_FILENAME),
        ]

        MULTI_EMBLEM_PARTY = dict(FAKE_PARTY_DICT)
        MULTI_EMBLEM_PARTY["PartyEmblems"].append(
            {
                "PartyEmblemId": 1,
                "MonochromeDescription": "Default Emblem",
                "Id": 1,
            }
        )
        MULTI_EMBLEM_PARTY["PartyEmblems"].append(
            {
                "PartyEmblemId": 0,
                "MonochromeDescription": "Not this one",
                "Id": 0,
            }
        )
        MULTI_EMBLEM_RESULTS_DICT = dict(FAKE_RESULTS_DICT)
        MULTI_EMBLEM_RESULTS_DICT["Results"] = [MULTI_EMBLEM_PARTY]
        FakeGetPartyList.return_value = MULTI_EMBLEM_RESULTS_DICT
        cmd = Command()

        out = StringIO()
        cmd.stdout = out

        self.assertEqual(PartyEmblem.objects.count(), 0)
        cmd.handle(
            **{
                "clear_emblems": False,
                "skip_create_joint": False,
                "post_to_slack": False,
                "quiet": False,
            }
        )
        self.assertEqual(PartyEmblem.objects.count(), 3)
        self.assertEqual(
            Party.objects.get(ec_id="PP01").default_emblem.description,
            "Default Emblem",
        )

    @patch.dict(
        "parties.importer.CORRECTED_PARTY_NAMES_IN_DESC",
        {"The Wombles Alliance": "Wombles Alliance"},
        clear=True,
    )
    def test_create_joint_parties(self):
        p1 = PartyFactory(ec_id="PP01", name="Wombles Alliance")
        p2 = PartyFactory(ec_id="PP02", name="Froglets Party")
        PartyDescriptionFactory(
            party=p2,
            description="Stop motion coalition (Joint description with The Wombles Alliance)",
            date_description_approved="2011-01-01",
        )
        PartyDescriptionFactory(
            party=p1,
            description="Stop motion coalition (Joint description with Froglets Party)",
            date_description_approved="2011-02-01",
        )

        self.assertEqual(Party.objects.all().count(), 4)
        importer = ECPartyImporter()

        importer.create_joint_parties()

        self.assertEqual(Party.objects.all().count(), 5)
        self.assertEqual(
            Party.objects.get(name="Stop motion coalition").ec_id,
            "joint-party:1-2",
        )
        self.assertTrue(len(importer.collector), 3)
