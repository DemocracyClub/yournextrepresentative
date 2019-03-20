from django_webtest import WebTest

from candidates.tests import factories
from candidates.tests.auth import TestUserMixin
from candidates.tests.uk_examples import UK2015ExamplesMixin
from parties.models import Party
from .factories import PartyDescriptionFactory


class TestPartyChoices(TestUserMixin, UK2015ExamplesMixin, WebTest):
    def test_hardly_any_candidates_at_all(self):
        party_choices = Party.objects.register("GB").party_choices()
        self.assertEqual(
            party_choices,
            [
                (u"", u""),
                (self.conservative_party.ec_id, u"Conservative Party"),
                (self.green_party.ec_id, u"Green Party"),
                ("ynmp-party:2", "Independent"),
                (self.labour_party.ec_id, u"Labour Party"),
                (self.ld_party.ec_id, u"Liberal Democrats"),
                ("ynmp-party:12522", "Speaker seeking re-election"),
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
                (u"", u""),
                (str(self.labour_party.ec_id), u"Labour Party"),
                (str(self.ld_party.ec_id), u"Liberal Democrats"),
                (str(self.conservative_party.ec_id), u"Conservative Party"),
                (str(self.green_party.ec_id), u"Green Party"),
                ("ynmp-party:2", "Independent"),
                ("ynmp-party:12522", "Speaker seeking re-election"),
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
                (u"", u""),
                (str(self.ld_party.ec_id), u"Liberal Democrats"),
                (str(self.green_party.ec_id), u"Green Party"),
                (str(self.conservative_party.ec_id), u"Conservative Party"),
                ("ynmp-party:2", "Independent"),
                (str(self.labour_party.ec_id), "Labour Party"),
                ("ynmp-party:12522", "Speaker seeking re-election"),
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
                (u"", u""),
                (
                    u"Liberal Democrats",
                    [
                        (self.ld_party.ec_id, u"Liberal Democrats"),
                        (
                            str(self.ld_party.ec_id),
                            u"Scottish Liberal Democrats",
                        ),
                    ],
                ),
                (str(self.green_party.ec_id), u"Green Party"),
                (str(self.conservative_party.ec_id), u"Conservative Party"),
                ("ynmp-party:2", "Independent"),
                (str(self.labour_party.ec_id), u"Labour Party"),
                ("ynmp-party:12522", "Speaker seeking re-election"),
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
                (u"", u""),
                (str(self.conservative_party.ec_id), u"Conservative Party"),
                (str(self.ld_party.ec_id), u"Liberal Democrats"),
                (str(self.green_party.ec_id), u"Green Party"),
                (str(self.labour_party.ec_id), u"Labour Party"),
                ("ynmp-party:2", "Independent"),
                ("ynmp-party:12522", "Speaker seeking re-election"),
            ],
        )
