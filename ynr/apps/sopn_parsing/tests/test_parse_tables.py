import json
from unittest import skipIf
from unittest.mock import patch

from bulk_adding.models import RawPeople
from candidates.tests.uk_examples import UK2015ExamplesMixin
from django.core.management import call_command
from django.test import TestCase
from official_documents.models import OfficialDocument
from pandas import Index, Series
from parties.models import Party
from parties.tests.factories import PartyFactory
from parties.tests.fixtures import DefaultPartyFixtures
from sopn_parsing.helpers import parse_tables
from sopn_parsing.models import ParsedSOPN
from sopn_parsing.tests import should_skip_pdf_tests
from sopn_parsing.tests.data.welsh_sopn_data import welsh_sopn_data

from ynr.apps.sopn_parsing.management.commands.sopn_parsing_parse_tables import (
    Command as ParseTablesCommand,
)


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

    @skipIf(should_skip_pdf_tests(), "Required PDF libs not installed")
    def test_welsh_run_sopn(self):
        """
        Test that if the ballot is welsh run and previous party affiliations
        are included they are parsed
        """
        self.assertFalse(RawPeople.objects.exists())
        doc = OfficialDocument.objects.create(
            ballot=self.senedd_ballot,
            document_type=OfficialDocument.NOMINATION_PAPER,
            source_url="example.com",
            relevant_pages="all",
        )

        plaid_cymru, _ = Party.objects.update_or_create(
            ec_id="PP77",
            legacy_slug="party:77",
            defaults={
                "name": "Plaid Cymru - The Party of Wales",
                "date_registered": "1999-01-14",
            },
        )

        dataframe = json.dumps(welsh_sopn_data)
        ParsedSOPN.objects.create(
            sopn=doc, raw_data=dataframe, status="unparsed"
        )
        call_command("sopn_parsing_parse_tables")
        self.assertEqual(RawPeople.objects.count(), 1)
        raw_people = RawPeople.objects.get()
        self.assertEqual(
            raw_people.data,
            [
                {
                    "name": "John Smith",
                    "party_id": self.conservative_party.ec_id,
                    "previous_party_affiliations": [self.ld_party.ec_id],
                },
                {
                    "name": "Joe Bloggs",
                    "party_id": self.labour_party.ec_id,
                    "previous_party_affiliations": ["ynmp-party:2"],
                },
                {"name": "Jon Doe", "party_id": self.ld_party.ec_id},
                {
                    "name": "Jane Brown",
                    "party_id": "ynmp-party:2",
                    "previous_party_affiliations": [plaid_cymru.ec_id],
                },
                {
                    "name": "Judy Johnson",
                    "party_id": plaid_cymru.ec_id,
                    "previous_party_affiliations": [self.labour_party.ec_id],
                },
                {"name": "Julie Williams", "party_id": "ynmp-party:2"},
            ],
        )


class TestParseTablesUnitTests(UK2015ExamplesMixin, TestCase):
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
                "expected_name": "Elaine Sheila Bagshaw",
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
                "expected_name": "Elaine Sheila Bagshaw",
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
                "expected_name": "Elaine Sheila Bagshaw",
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
                "expected_name": "Elaine Sheila Bagshaw",
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
                assert name == "Elaine Sheila Bagshaw"

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
            ("DAVE Nitesh Pravin", "Nitesh Pravin Dave"),
            ("DAVE\nNitesh Pravin", "Nitesh Pravin Dave"),
            ("COOKE Anne-Marie", "Anne-Marie Cooke"),
            ("COOKE\nAnne-Marie", "Anne-Marie Cooke"),
            ("BROOKES-\nDUNCAN\nKaty", "Katy Brookes-Duncan"),
            ("HOUNSOME\nJohn", "John Hounsome"),
            ("O`CONNELL \nStephen John", "Stephen John O'Connell"),
            ("O`NEAL \nCarol Joy", "Carol Joy O'Neal"),
            ("O`REILLY \nTracey Linda \nDiane", "Tracey Linda Diane O'Reilly"),
            ("LIAM THOMAS O'ROURKE", "Liam Thomas O'Rourke"),
            ("O'CALLAGHAN \nClaire Louise", "Claire Louise O'Callaghan"),
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

    def test_guess_previous_party_affiliations_field(self):
        sopn = ParsedSOPN(raw_data=json.dumps(welsh_sopn_data))
        data = sopn.as_pandas
        data.columns = data.iloc[0]

        cases = [
            (self.dulwich_post_ballot, None),
            (self.senedd_ballot, "statement of party membership"),
        ]
        for case in cases:
            with self.subTest(msg=case[0]):
                sopn.sopn = OfficialDocument(ballot=case[0])
                result = parse_tables.guess_previous_party_affiliations_field(
                    data=data, sopn=sopn
                )
                assert result == case[1]

    def test_add_previous_party_affiliations(self):
        cases = [
            {"party_str": "", "party": None, "expected": {}},
            {"party_str": "Unknown Party", "party": None, "expected": {}},
            {
                "party_str": "Labour Party",
                "party": self.labour_party,
                "expected": {
                    "previous_party_affiliations": [self.labour_party.ec_id]
                },
            },
        ]
        for case in cases:
            with self.subTest(msg=case["party_str"]), patch.object(
                parse_tables, "get_party", return_value=case["party"]
            ):
                raw_data = {}
                sopn = ParsedSOPN()
                result = parse_tables.add_previous_party_affiliations(
                    party_str=case["party_str"],
                    raw_data=raw_data,
                    sopn=sopn,
                )
                assert result == case["expected"]


class TestParseTablesFilterKwargs(TestCase):
    def setUp(self):
        self.command = ParseTablesCommand()
        self.default_filter_kwargs = {
            "officialdocument__parsedsopn__isnull": False
        }

    def test_when_testing(self):
        options = {"testing": True}
        result = self.command.build_filter_kwargs(options)
        self.assertEqual(result, self.default_filter_kwargs)

    def test_when_using_ballot(self):
        options = {"ballot": "local.foo.bar.2021-05-06"}
        result = self.command.build_filter_kwargs(options)
        self.assertEqual(result, self.default_filter_kwargs)

    def test_when_using_reparse(self):
        options = {"reparse": True}
        result = self.command.build_filter_kwargs(options)
        expected = self.default_filter_kwargs.copy()
        expected["rawpeople__source_type"] = RawPeople.SOURCE_PARSED_PDF
        self.assertEqual(result, expected)

    def test_when_no_options(self):
        options = {}
        result = self.command.build_filter_kwargs(options)
        expected = self.default_filter_kwargs.copy()
        expected["officialdocument__parsedsopn__parsed_data"] = None
        expected["officialdocument__parsedsopn__status"] = "unparsed"
        self.assertEqual(result, expected)
