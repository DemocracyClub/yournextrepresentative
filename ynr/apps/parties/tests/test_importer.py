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
            "Make Good Use of Bad Rubbish | Gwneud Defnydd Da o Sbwriel Gwael",
        )
        self.assertEqual(party_model.emblems.count(), 1)
        self.assertEqual(
            party_model.default_emblem.description, "Box containing the word"
        )

    def test_raises_on_bad_dict(self):
        with self.assertRaises(ValueError):
            ECParty({})

    @patch("parties.importer.ECPartyImporter.get_party_list")
    @patch.dict("parties.importer.DEFAULT_EMBLEMS", {
            "PP01": 1
        }, clear=True)
    def test_set_emblem_default(self, FakeGetPartyList):
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
        cmd.handle(**{"output_new_parties": True, "clear_emblems": True})
        self.assertEqual(PartyEmblem.objects.count(), 3)
        self.assertEqual(
            Party.objects.first().default_emblem.description, "Default Emblem"
        )
