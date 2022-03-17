from unittest.mock import PropertyMock, patch
from django.test import TestCase
from candidates.models.popolo_extra import Ballot
from candidates.tests.factories import MembershipFactory
from candidates.tests.uk_examples import UK2015ExamplesMixin

from parties.tests.fixtures import DefaultPartyFixtures
from people.forms.forms import PersonMembershipForm
from people.tests.factories import PersonFactory


class TestPersonMembershipForm(
    UK2015ExamplesMixin, DefaultPartyFixtures, TestCase
):
    def test_show_previous_party_affiliations_called_on_init(self):
        with patch.object(
            PersonMembershipForm,
            "show_previous_party_affiliations",
            new_callable=PropertyMock,
        ) as mock:
            mock.return_value = False
            PersonMembershipForm()
            mock.assert_called_once()

    def test_show_previous_party_affiliations(self):

        # test without a membership instance
        form = PersonMembershipForm()
        self.assertFalse(form.show_previous_party_affiliations)

        # without a welsh-run ballot
        non_welsh_membership = MembershipFactory(
            ballot=self.dulwich_post_ballot,
            person=PersonFactory(),
            party=self.labour_party,
        )
        form = PersonMembershipForm(instance=non_welsh_membership)
        self.assertFalse(form.show_previous_party_affiliations)

        welsh_membership = MembershipFactory(
            ballot=self.senedd_ballot,
            person=PersonFactory(),
            party=self.labour_party,
        )
        # with a welsh-run ballot, but candidates locked
        self.senedd_ballot.candidates_locked = True
        self.senedd_ballot.save()
        form = PersonMembershipForm(instance=welsh_membership)
        self.assertFalse(form.show_previous_party_affiliations)

        # with a welsh-run ballot, candidates not locked, but no SOPN
        self.senedd_ballot.candidates_locked = False
        self.senedd_ballot.save()
        form = PersonMembershipForm(instance=welsh_membership)
        self.assertFalse(form.show_previous_party_affiliations)

        # with a welsh-run ballot, candidates not locked, has SOPN
        self.senedd_ballot.candidates_locked = False
        self.senedd_ballot.save()
        # mock the sopn property to save creating an OfficialDocument
        with patch.object(Ballot, "sopn", new_callable=PropertyMock) as mock:
            mock.return_value = True
            form = PersonMembershipForm(instance=welsh_membership)
            self.assertTrue(form.show_previous_party_affiliations)
