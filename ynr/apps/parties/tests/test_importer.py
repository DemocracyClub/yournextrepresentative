"""
Test some of the basic model use cases

"""
from mock import patch
from io import StringIO

from django.test import TestCase
from django.core.files.storage import DefaultStorage

from candidates.tests.helpers import TmpMediaRootMixin
from moderation_queue.tests.paths import EXAMPLE_IMAGE_FILENAME

from parties.importer import ECParty, ECPartyImporter
from parties.models import Party, PartyDescription, PartyEmblem
from parties.management.commands.parties_import_from_ec import Command


FAKE_PARTY_DICT = {
    "RegulatedEntityName": "Wombles Alliance",
    "ECRef": "PP01",
    "RegisterName": "Great Britain",
    "RegistrationStatusName": "Registered",
    "ApprovedDate": "/Date(1134345600000)/",
    "PartyDescriptions": [
        {
            "Description": "Wombling for a better future",
            "Translation": "Wombling am well dyfodol",
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


class TestECPartyImporter(TmpMediaRootMixin, TestCase):
    def setUp(self):
        super().setUp()
        self.storage = DefaultStorage()

    @patch("parties.importer.ECPartyImporter.get_party_list")
    def test_importer(self, FakeGetPartyList):
        FakeGetPartyList.return_value = FAKE_RESULTS_DICT
        importer = ECPartyImporter()
        new_parties = importer.do_import()
        self.assertEqual(Party.objects.count(), 1)
        self.assertEqual(new_parties[0].name, "Wombles Alliance")

    @patch("parties.importer.ECPartyImporter.get_party_list")
    def test_import_management_command(self, FakeGetPartyList):
        FakeGetPartyList.return_value = FAKE_RESULTS_DICT
        cmd = Command()

        out = StringIO()
        cmd.stdout = out
        cmd.handle(**{"output_new_parties": True, "clear_emblems": True})
        self.assertTrue(
            cmd.stdout.getvalue().startswith("Found new political parties!")
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
        FakeEmblemPath.return_value = EXAMPLE_IMAGE_FILENAME
        self.assertFalse(Party.objects.all().exists())
        self.assertFalse(PartyDescription.objects.all().exists())
        self.assertFalse(PartyEmblem.objects.all().exists())
        party = ECParty(FAKE_PARTY_DICT)
        party.save()
        self.assertEqual(Party.objects.count(), 1)
        party_model = Party.objects.get(ec_id="PP01")
        self.assertEqual(party_model.name, "Wombles Alliance")
        self.assertEqual(party_model.register, "GB")
        self.assertEqual(party_model.status, "Registered")
        self.assertEqual(
            party_model.descriptions.first().description,
            "Wombling for a better future | Wombling am well dyfodol",
        )
        self.assertEqual(party_model.emblems.count(), 1)
        self.assertEqual(
            party_model.default_emblem.description, "Box containing the word"
        )

    def test_raises_on_bad_dict(self):
        with self.assertRaises(ValueError):
            ECParty({})
