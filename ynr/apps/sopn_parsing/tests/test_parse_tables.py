import json

from django.core.management import call_command
from django.test import TestCase

from bulk_adding.models import RawPeople
from candidates.tests.uk_examples import UK2015ExamplesMixin
from official_documents.models import OfficialDocument
from parties.tests.factories import PartyFactory
from parties.tests.fixtures import DefaultPartyFixtures
from sopn_parsing.models import ParsedSOPN
from sopn_parsing.helpers import parse_tables
from unittest import skipIf
from pandas import Index, Series

from sopn_parsing.tests import should_skip_pdf_tests


class TestSOPNHelpers(DefaultPartyFixtures, UK2015ExamplesMixin, TestCase):
    def setUp(self):
        PartyFactory(ec_id="PP85", name="UK Independence Party (UKIP)")

    @skipIf(should_skip_pdf_tests(), "Required PDF libs not installed")
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
                    "5": "Name of \nCandidate",
                },
                "1": {
                    "0": "Home Address",
                    "1": "10 Fowey Close, \nShoreham by Sea, \nWest Sussex, \nBN43 5HE",
                    "2": "51 Old Fort Road, \nShoreham by Sea, \nBN43 5RL",
                    "3": "76 Harbour Way, \nShoreham by Sea, \nSussex, \nBN43 5HH",
                    "4": "9 Flag Square, \nShoreham by Sea, \nWest Sussex, \nBN43 5RZ",
                    "5": "Home Address",
                },
                "2": {
                    "0": "Description (if \nany)",
                    "1": "Green Party",
                    "2": "Independent",
                    "3": "UK Independence \nParty (UKIP)",
                    "4": "Labour Party",
                    "5": "Description (if \nany)",
                },
                "3": {
                    "0": "Name of \nProposer",
                    "1": "Tiffin Susan J",
                    "2": "Loader Jocelyn C",
                    "3": "Hearne James H",
                    "4": "O`Connor Lavinia",
                    "5": "Name of \nProposer",
                },
                "4": {
                    "0": "Reason \nwhy no \nlonger \nnominated\n*",
                    "1": "",
                    "2": "",
                    "3": "",
                    "4": "",
                    "5": "Reason \nwhy no \nlonger \nnominated\n*",
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


class TestParseTablesUnitTests(TestCase):
    def get_two_name_field_cases(self):
        # this could be updated with more combinations as we come across them
        return [
            {
                "name_fields": ["candidate surname", "candidate forename"],
                "row": {
                    "candidate surname": "BAGSHAW",
                    "candidate forename": "Elaine Sheila",
                    "home address": "1 Foo Street \n London \nE14 6FW",
                    "description": "London Liberal \nDemocrats",
                    "reason why no longer nominated": "",
                },
                "ordered_name_fields": [
                    "candidate forename",
                    "candidate surname",
                ],
                "expected_name": "BAGSHAW Elaine Sheila",
            },
            {
                "name_fields": ["surname", "other names"],
                "row": {
                    "surname": "BAGSHAW",
                    "other names": "Elaine Sheila",
                    "home address": "1 Foo Street \nLondon \nE14 6FW",
                    "description": "London Liberal \nDemocrats",
                    "reason why no longer nominated": "",
                },
                "ordered_name_fields": ["other names", "surname"],
                "expected_name": "BAGSHAW Elaine Sheila",
            },
            {
                "name_fields": ["last name", "other names"],
                "row": {
                    "last name": "BAGSHAW",
                    "other names": "Elaine Sheila",
                    "home address": "1 Foo Street \nLondon \nE14 6FW",
                    "description": "London Liberal \nDemocrats",
                    "reason why no longer nominated": "",
                },
                "ordered_name_fields": ["other names", "last name"],
                "expected_name": "BAGSHAW Elaine Sheila",
            },
            {
                "name_fields": ["candidate forename", "candidate surname"],
                "row": {
                    "candidate forename": "Elaine Sheila",
                    "candidate surname": "BAGSHAW",
                    "home address": "1 Foo Street \n London \nE14 6FW",
                    "description": "London Liberal \nDemocrats",
                    "reason why no longer nominated": "",
                },
                "ordered_name_fields": [
                    "candidate forename",
                    "candidate surname",
                ],
                "expected_name": "Elaine Sheila BAGSHAW",
            },
        ]

    def get_single_name_field_cases(self):
        return [
            {
                "name_fields": ["name of candidate"],
                "row": {
                    "name of candidate": "BAGSHAW Elaine Sheila",
                    "home address": "1 Foo Street \n London \nE14 6FW",
                    "description": "London Liberal \nDemocrats",
                    "reason why no longer nominated": "",
                },
            },
            {
                "name_fields": ["names of candidate"],
                "row": {
                    "names of candidate": "BAGSHAW Elaine Sheila",
                    "home address": "1 Foo Street \nLondon \nE14 6FW",
                    "description": "London Liberal \nDemocrats",
                    "reason why no longer nominated": "",
                },
            },
            {
                "name_fields": ["candidate name"],
                "row": {
                    "candidate name": "BAGSHAW Elaine Sheila",
                    "home address": "1 Foo Street \nLondon \nE14 6FW",
                    "description": "London Liberal \nDemocrats",
                    "reason why no longer nominated": "",
                },
            },
            {
                "name_fields": ["surname"],
                "row": {
                    "surname": "BAGSHAW Elaine Sheila",
                    "home address": "1 Foo Street \nLondon \nE14 6FW",
                    "description": "London Liberal \nDemocrats",
                    "reason why no longer nominated": "",
                },
            },
            {
                "name_fields": ["candidates surname"],
                "row": {
                    "candidates surname": "BAGSHAW Elaine Sheila",
                    "home address": "1 Foo Street \nLondon \nE14 6FW",
                    "description": "London Liberal \nDemocrats",
                    "reason why no longer nominated": "",
                },
            },
            {
                "name_fields": ["other name"],
                "row": {
                    "other name": "BAGSHAW Elaine Sheila",
                    "home address": "1 Foo Street \nLondon \nE14 6FW",
                    "description": "London Liberal \nDemocrats",
                    "reason why no longer nominated": "",
                },
            },
        ]

    def test_get_name_single_field(self):
        for case in self.get_single_name_field_cases():
            row = Series(case["row"])
            name_fields = case["name_fields"]
            with self.subTest(name_fields=name_fields):
                assert len(case["name_fields"]) == 1
                name = parse_tables.get_name(row=row, name_fields=name_fields)
                assert name == "BAGSHAW Elaine Sheila"

    def test_get_name_two_fields(self):
        for case in self.get_two_name_field_cases():
            row = Series(case["row"])
            name_fields = case["name_fields"]
            with self.subTest(name_fields=name_fields):
                assert len(case["name_fields"]) == 2
                name = parse_tables.get_name(row=row, name_fields=name_fields)
                assert name == case["expected_name"]

    def test_get_name_fields_single(self):
        for case in self.get_single_name_field_cases():
            row = Index(case["row"])
            with self.subTest(row=row):
                name_fields = parse_tables.get_name_fields(row=row)
                assert len(name_fields) == 1
                assert name_fields == case["name_fields"]

    def test_get_name_fields_two(self):
        for case in self.get_two_name_field_cases():
            row = Index(case["row"])
            with self.subTest(row=row):
                name_fields = parse_tables.get_name_fields(row=row)
                assert len(name_fields) == 2
                assert name_fields == case["name_fields"]

    def test_get_name_fields_raises_error(self):
        row = Index({"foo": "Bar"})
        with self.assertRaises(ValueError):
            parse_tables.get_name_fields(row=row)

    def test_order_name_fields(self):
        for case in self.get_two_name_field_cases():
            name_fields = case["name_fields"]
            with self.subTest(name_fields=name_fields):
                result = parse_tables.order_name_fields(name_fields)
                assert result == case["ordered_name_fields"]

    def test_clean_name_replaces_backticks(self):
        name = parse_tables.clean_name("D`SOUZA")
        assert "`" not in name
        assert "'" in name

    def test_clean_name_replaces_newlines(self):
        name = parse_tables.clean_name(
            "A Very Long Name That Splits \nOver Lines"
        )
        assert "\n" not in name

    def test_clean_name_capitalized_last_and_titalized(self):
        name = parse_tables.clean_name("SMITH John")
        assert name == "John Smith"

    def test_clean_last_names(self):
        name = parse_tables.clean_last_names(["MACDONALD", "John"])
        assert name == "MacDonald"

    def test_clean_name_two_word_surnames(self):
        names = [
            ("EDE COOPER \nPalmer", "Palmer Ede Cooper"),
            ("VAN DULKEN \nRichard Michael", "Richard Michael Van Dulken"),
            ("ARMSTRONG LILLEY \nLynne", "Lynne Armstrong Lilley"),
            (
                " D`SOUZA  Aaron Anthony Jose \nHasan",
                "Aaron Anthony Jose Hasan D'Souza",
            ),
            ("Michael James Collins", "Michael James Collins"),
            ("   Michael    James    Collins   ", "Michael James Collins"),
        ]
        for name in names:
            with self.subTest(name=names[0]):
                assert parse_tables.clean_name(name[0]) == name[1]

    def test_clean_description_removes_newlines(self):
        cleaned_description = parse_tables.clean_description(
            "A Long Description That Splits \nOver \\nLines"
        )
        assert "\n" not in cleaned_description
        assert "\\n" not in cleaned_description

    def test_clean_description_replaces_backticks(self):
        cleaned_description = parse_tables.clean_description(
            "All People`s Party"
        )
        assert "`" not in cleaned_description
        assert "'" in cleaned_description
        assert cleaned_description == "All People's Party"
