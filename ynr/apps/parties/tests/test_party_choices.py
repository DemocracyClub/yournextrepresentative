from django_webtest import WebTest

from candidates.tests.auth import TestUserMixin
from candidates.tests.uk_examples import UK2015ExamplesMixin
from parties.models import Party
from parties.tests.fixtures import DefaultPartyFixtures

from .factories import PartyDescriptionFactory


class TestPartyChoices(
    DefaultPartyFixtures, TestUserMixin, UK2015ExamplesMixin, WebTest
):
    maxDiff = None

    def test_hardly_any_candidates_at_all(self):
        party_choices = Party.objects.register("GB").party_choices()
        self.assertEqual(
            party_choices,
            [
                ("", {"label": ""}),
                (
                    self.conservative_party.ec_id,
                    {"label": "Conservative Party", "register": "GB"},
                ),
                (
                    self.green_party.ec_id,
                    {"label": "Green Party", "register": "GB"},
                ),
                ("ynmp-party:2", {"label": "Independent", "register": "all"}),
                (
                    self.labour_party.ec_id,
                    {"label": "Labour Party", "register": "GB"},
                ),
                (
                    self.ld_party.ec_id,
                    {"label": "Liberal Democrats", "register": "GB"},
                ),
                (
                    "ynmp-party:12522",
                    {"label": "Speaker seeking re-election", "register": "all"},
                ),
            ],
        )

    def test_only_candidates_in_earlier_election(self):
        self.create_lots_of_candidates(
            self.earlier_election, ((self.labour_party, 16), (self.ld_party, 8))
        )
        party_choices = Party.objects.register("GB").party_choices()
        self.assertEqual(
            party_choices,
            [
                ("", {"label": ""}),
                (
                    self.labour_party.ec_id,
                    {"label": "Labour Party", "register": "GB"},
                ),
                (
                    self.ld_party.ec_id,
                    {"label": "Liberal Democrats", "register": "GB"},
                ),
                (
                    self.conservative_party.ec_id,
                    {"label": "Conservative Party", "register": "GB"},
                ),
                (
                    self.green_party.ec_id,
                    {"label": "Green Party", "register": "GB"},
                ),
                ("ynmp-party:2", {"label": "Independent", "register": "all"}),
                (
                    "ynmp-party:12522",
                    {"label": "Speaker seeking re-election", "register": "all"},
                ),
            ],
        )

    def test_enough_candidates_in_current_election(self):
        self.create_lots_of_candidates(
            self.election, ((self.ld_party, 30), (self.green_party, 15))
        )

        party_choices = Party.objects.register("GB").party_choices()
        self.assertEqual(
            party_choices,
            [
                ("", {"label": ""}),
                (
                    self.ld_party.ec_id,
                    {"label": "Liberal Democrats", "register": "GB"},
                ),
                (
                    self.green_party.ec_id,
                    {"label": "Green Party", "register": "GB"},
                ),
                (
                    self.conservative_party.ec_id,
                    {"label": "Conservative Party", "register": "GB"},
                ),
                ("ynmp-party:2", {"label": "Independent", "register": "all"}),
                (
                    self.labour_party.ec_id,
                    {"label": "Labour Party", "register": "GB"},
                ),
                (
                    "ynmp-party:12522",
                    {"label": "Speaker seeking re-election", "register": "all"},
                ),
            ],
        )

    def test_other_names_in_party_choices(self):
        self.create_lots_of_candidates(
            self.election, ((self.ld_party, 30), (self.green_party, 15))
        )
        PartyDescriptionFactory(
            party=self.ld_party, description="Scottish Liberal Democrats"
        )
        party_choices = Party.objects.register("GB").party_choices()
        self.assertEqual(
            party_choices,
            [
                ("", {"label": ""}),
                (
                    "Liberal Democrats",
                    [
                        (
                            "PP90",
                            {"label": "Liberal Democrats", "register": "GB"},
                        ),
                        (
                            "PP90",
                            {
                                "label": "Scottish Liberal Democrats",
                                "register": "GB",
                            },
                        ),
                    ],
                ),
                (
                    self.green_party.ec_id,
                    {"label": "Green Party", "register": "GB"},
                ),
                (
                    self.conservative_party.ec_id,
                    {"label": "Conservative Party", "register": "GB"},
                ),
                ("ynmp-party:2", {"label": "Independent", "register": "all"}),
                (
                    self.labour_party.ec_id,
                    {"label": "Labour Party", "register": "GB"},
                ),
                (
                    "ynmp-party:12522",
                    {"label": "Speaker seeking re-election", "register": "all"},
                ),
            ],
        )

    def test_enough_candidates_in_current_election_with_past_election(self):
        self.create_lots_of_candidates(
            self.election, ((self.ld_party, 30), (self.green_party, 15))
        )
        self.create_lots_of_candidates(
            self.earlier_election,
            ((self.conservative_party, 30), (self.labour_party, 15)),
        )
        party_choices = Party.objects.register("GB").party_choices()
        self.assertEqual(
            party_choices,
            [
                ("", {"label": ""}),
                (
                    self.conservative_party.ec_id,
                    {"label": "Conservative Party", "register": "GB"},
                ),
                (
                    self.ld_party.ec_id,
                    {"label": "Liberal Democrats", "register": "GB"},
                ),
                (
                    self.green_party.ec_id,
                    {"label": "Green Party", "register": "GB"},
                ),
                (
                    self.labour_party.ec_id,
                    {"label": "Labour Party", "register": "GB"},
                ),
                ("ynmp-party:2", {"label": "Independent", "register": "all"}),
                (
                    "ynmp-party:12522",
                    {"label": "Speaker seeking re-election", "register": "all"},
                ),
            ],
        )
