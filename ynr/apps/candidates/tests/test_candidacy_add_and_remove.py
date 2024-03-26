from django_webtest import WebTest
from official_documents.models import BallotSOPN
from people.tests.factories import PersonFactory

from ..models import Ballot
from .auth import TestUserMixin
from .factories import MembershipFactory
from .uk_examples import UK2015ExamplesMixin


class TestCandidacyCreateView(TestUserMixin, UK2015ExamplesMixin, WebTest):
    def setUp(self):
        super().setUp()
        self.person = PersonFactory.create(id=2009, name="Tessa Jowell")
        MembershipFactory.create(
            person=self.person,
            post=self.camberwell_post,
            party=self.labour_party,
            ballot=self.camberwell_post_ballot_earlier,
        )

    def test_create_candidacy_from_earlier_election(self):
        self.assertEqual(self.person.memberships.count(), 1)
        response = self.app.get(
            self.camberwell_post_ballot.get_absolute_url(),
            user=self.user_who_can_lock,
        )
        form = response.forms["candidacy-create_{}".format(self.person.pk)]
        form["source"] = "Tests"
        form.submit()
        self.assertEqual(self.person.memberships.count(), 2)


class TestCandidacyDeleteView(TestUserMixin, UK2015ExamplesMixin, WebTest):
    def setUp(self):
        super().setUp()
        self.person = PersonFactory.create(id=2009, name="Tessa Jowell")

        MembershipFactory.create(
            person=self.person,
            post=self.dulwich_post,
            party=self.green_party,
            ballot=self.dulwich_post_ballot,
        )

    def test_delete_candidacy(self):
        self.assertEqual(self.person.memberships.count(), 1)
        response = self.app.get(
            self.dulwich_post_ballot.get_absolute_url(),
            user=self.user_who_can_lock,
        )
        form = response.forms["candidacy-delete_{}".format(self.person.pk)]
        form["source"] = "Tests"
        form.submit()
        self.assertEqual(self.person.memberships.count(), 0)


class TestEditButtonsShown(TestUserMixin, UK2015ExamplesMixin, WebTest):
    def test_can_see_add_button_with_no_sopn(self):
        ballot: Ballot = self.dulwich_post_ballot
        response = self.app.get(
            ballot.get_absolute_url(),
            user=self.user,
        )
        self.assertContains(response, "Add a new candidate")
        BallotSOPN.objects.create(ballot=ballot)
        response = self.app.get(
            ballot.get_absolute_url(),
            user=self.user,
        )
        self.assertNotContains(response, "Add a new candidate")
