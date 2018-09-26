from django_webtest import WebTest

from .auth import TestUserMixin
from .uk_examples import UK2015ExamplesMixin
from .factories import MembershipFactory, PersonFactory


class TestCandidacyDeleteView(TestUserMixin, UK2015ExamplesMixin, WebTest):
    def setUp(self):
        super().setUp()
        self.person = PersonFactory.create(id="2009", name="Tessa Jowell")

        MembershipFactory.create(
            person=self.person,
            post=self.dulwich_post,
            party=self.green_party,
            post_election=self.dulwich_post_pee,
        )

    def test_delete_candidacy(self):
        self.assertEqual(self.person.memberships.count(), 1)
        response = self.app.get(
            self.dulwich_post_pee.get_absolute_url(),
            user=self.user_who_can_lock,
        )
        form = response.forms["source-confirmation-not-standing"]
        form["source"] = "Tests"
        form.submit()
        self.assertEqual(self.person.memberships.count(), 0)
