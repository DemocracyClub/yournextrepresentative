from django.test import TestCase
from unittest.mock import PropertyMock, patch
from candidates.tests.factories import BallotPaperFactory
from candidates.tests.uk_examples import UK2015ExamplesMixin
from parties.tests.factories import PartyFactory
from people.tests.factories import PersonFactory
from popolo.models import Membership, WelshOnlyValidationError


class AddingPreviousPartyAffiliatiopns(UK2015ExamplesMixin, TestCase):
    def setUp(self):
        new_candidate = PersonFactory.create(name="John Doe")
        party = PartyFactory()
        ballot = BallotPaperFactory()
        self.old_party = PartyFactory()
        self.membership = Membership.objects.create(
            person=new_candidate, party=party, post=ballot.post, ballot=ballot
        )

    def test_can_add_affiliation(self):
        with patch(
            "candidates.models.Ballot.is_welsh_run",
            new_callable=PropertyMock,
            return_value=True,
        ):
            self.membership.previous_party_affiliations.add(self.old_party)
            self.assertEqual(
                self.membership.previous_party_affiliations.first(),
                self.old_party,
            )

    @patch("candidates.models.Ballot.is_welsh_run", new_callable=PropertyMock)
    def test_cannot_add_affiliation(self, is_welsh_run):
        is_welsh_run.return_value = False
        with self.assertRaises(WelshOnlyValidationError):
            self.membership.previous_party_affiliations.add(self.old_party)
