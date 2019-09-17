import json

from django.core.management import call_command
from django.test import TestCase

from bulk_adding.models import RawPeople
from candidates.tests.uk_examples import UK2015ExamplesMixin
from official_documents.models import OfficialDocument
from parties.tests.factories import PartyFactory
from sopn_parsing.models import ParsedSOPN


class TestSOPNHelpers(UK2015ExamplesMixin, TestCase):
    def setUp(self):
        PartyFactory(ec_id="PP85", name="UK Independence Party (UKIP)")

    def test_basic_parsing(self):
        self.assertFalse(RawPeople.objects.exists())
        doc = OfficialDocument.objects.create(
            ballot=self.dulwich_post_ballot,
            document_type=OfficialDocument.NOMINATION_PAPER,
            source_url="example.com",
            relevant_pages="all",
        )
        dataframe = json.dumps(
            {
                "0": {
                    "0": "Name of \nCandidate",
                    "1": "BRADBURY \nAndrew John",
                    "2": "COLLINS \nDave",
                    "3": "HARVEY \nPeter John",
                    "4": "JENNER \nMelanie",
                },
                "1": {
                    "0": "Home Address",
                    "1": "10 Fowey Close, \nShoreham by Sea, \nWest Sussex, \nBN43 5HE",
                    "2": "51 Old Fort Road, \nShoreham by Sea, \nBN43 5RL",
                    "3": "76 Harbour Way, \nShoreham by Sea, \nSussex, \nBN43 5HH",
                    "4": "9 Flag Square, \nShoreham by Sea, \nWest Sussex, \nBN43 5RZ",
                },
                "2": {
                    "0": "Description (if \nany)",
                    "1": "Green Party",
                    "2": "Independent",
                    "3": "UK Independence \nParty (UKIP)",
                    "4": "Labour Party",
                },
                "3": {
                    "0": "Name of \nProposer",
                    "1": "Tiffin Susan J",
                    "2": "Loader Jocelyn C",
                    "3": "Hearne James H",
                    "4": "O`Connor Lavinia",
                },
                "4": {
                    "0": "Reason \nwhy no \nlonger \nnominated\n*",
                    "1": "",
                    "2": "",
                    "3": "",
                    "4": "",
                },
            }
        )
        ParsedSOPN.objects.create(
            sopn=doc, raw_data=dataframe, status="unparsed"
        )
        call_command("sopn_parsing_parse_tables")
        self.assertEqual(RawPeople.objects.count(), 1)
        raw_people = RawPeople.objects.get()
        self.assertEqual(
            raw_people.data,
            [
                {"name": "Andrew John Bradbury", "party_id": "PP63"},
                {"name": "Dave Collins", "party_id": "ynmp-party:2"},
                {"name": "Peter John Harvey", "party_id": "PP85"},
                {"name": "Melanie Jenner", "party_id": "PP53"},
            ],
        )
