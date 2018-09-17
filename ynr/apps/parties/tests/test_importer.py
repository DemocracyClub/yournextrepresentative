"""
Test some of the basic model use cases

"""
from mock import patch
from io import StringIO
from tempfile import NamedTemporaryFile

from django.test import TestCase
from django.core.files.storage import DefaultStorage

from candidates.tests.helpers import TmpMediaRootMixin
from moderation_queue.tests.paths import (
    EXAMPLE_IMAGE_FILENAME,
    BROKEN_IMAGE_FILENAME,
)

from parties.importer import ECParty, ECPartyImporter
from parties.models import Party, PartyDescription, PartyEmblem
from parties.management.commands.parties_import_from_ec import Command
from .factories import PartyFactory, PartyDescriptionFactory


FAKE_PARTY_DICT = {
    "RegulatedEntityName": "Wombles Alliance",
    "ECRef": "PP01",
    "RegisterName": "Great Britain",
    "RegistrationStatusName": "Registered",
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


class TestECPartyImporter(TmpMediaRootMixin, TestCase):
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

    @patch("parties.importer.ECEmblem.download_emblem")
    def test_save(self, FakeEmblemPath):
        FakeEmblemPath.return_value = make_tmp_file_from_source(
            EXAMPLE_IMAGE_FILENAME
        )
        self.assertEqual(Party.objects.count(), 2)
        self.assertEqual(PartyDescription.objects.count(), 0)
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
