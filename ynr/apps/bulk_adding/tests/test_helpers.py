from bulk_adding import helpers
from candidates.tests.auth import TestUserMixin
from candidates.tests.uk_examples import UK2015ExamplesMixin
from django.test.client import RequestFactory
from django_webtest import WebTest
from parties.tests.factories import PartyDescriptionFactory
from people.tests.factories import PersonFactory
from popolo.models import Membership


class TestBulkAddingByParty(TestUserMixin, UK2015ExamplesMixin, WebTest):
    def setUp(self):
        super().setUp()
        self.factory = RequestFactory()

    def test_add_person(self):
        request = self.factory.get("/")
        request.user = self.user

        person_data = {"name": "Foo", "source": "example.com"}

        with self.assertNumQueries(7):
            helpers.add_person(request, person_data)

    def test_update_person(self):
        """
        Test that person is updated. Checks that when a PartyDescription object
        is used values are used from it to set on the membership
        """
        request = self.factory.get("/")
        request.user = self.user

        party_description = PartyDescriptionFactory(
            party=self.green_party, description="Greens for Dulwich"
        )
        person = PersonFactory()
        for description in [None, party_description]:
            with self.subTest(description=description):
                helpers.update_person(
                    request=request,
                    person=person,
                    party=self.green_party,
                    ballot=self.dulwich_post_ballot,
                    list_position=1,
                    source="http://example.com",
                    party_description=description,
                )

                membership = Membership.objects.get(
                    person=person,
                    party=self.green_party,
                    ballot=self.dulwich_post_ballot,
                )
                self.assertEqual(membership.party_name, self.green_party.name)
                self.assertEqual(membership.party_list_position, 1)
                self.assertEqual(membership.party_list_position, 1)
                self.assertIsNone(membership.elected)
                self.assertEqual(membership.role, "Candidate")
                self.assertEqual(membership.party_description, description)
                self.assertEqual(
                    membership.party_description_text,
                    getattr(description, "description", ""),
                )
