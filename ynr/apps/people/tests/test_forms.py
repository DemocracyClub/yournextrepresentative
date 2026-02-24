from unittest.mock import PropertyMock, patch

from candidates.models.popolo_extra import Ballot
from candidates.tests.factories import MembershipFactory
from candidates.tests.uk_examples import UK2015ExamplesMixin
from django.test import TestCase
from parties.models import Party
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

    def test_party_identifier_initial_value_selected_with_party_description(
        self,
    ):
        # use independent for this test because it has 2 descriptions
        # [blank] and [No party listed]
        independent = Party.objects.get(ec_id="ynmp-party:2")

        membership = MembershipFactory(
            ballot=self.dulwich_post_ballot,
            person=PersonFactory(),
            party=independent,
            party_description=independent.descriptions.all().get(
                description="[No party listed]"
            ),
        )
        form = PersonMembershipForm(instance=membership)
        select_html = str(form["party_identifier"].as_widget())
        self.assertIn(
            '<option value="ynmp-party:2__1001" selected register="all">[No party listed]</option>',
            select_html,
        )

    def test_party_identifier_initial_value_selected_without_party_description(
        self,
    ):
        membership = MembershipFactory(
            ballot=self.dulwich_post_ballot,
            person=PersonFactory(),
            party=self.labour_party,
        )
        form = PersonMembershipForm(instance=membership)
        select_html = str(form["party_identifier"].as_widget())
        self.assertIn(
            '<option value="PP53" selected register="GB">Labour Party</option>',
            select_html,
        )
