from django.test import TestCase

from candidates.tests.factories import (
    ElectionFactory,
    MembershipFactory,
    ParliamentaryChamberFactory,
    PostFactory,
)
from people.tests.factories import PersonFactory
from candidates.tests.uk_examples import UK2015ExamplesMixin
from parties.tests.factories import PartyFactory


class TestFieldView(UK2015ExamplesMixin, TestCase):
    def setUp(self):
        super().setUp()

        person = PersonFactory.create(id=2009, name="Tessa Jowell")

        MembershipFactory.create(
            person=person,
            post=self.dulwich_post,
            party=self.green_party,
            post_election=self.dulwich_post_pee,
        )

        person = PersonFactory.create(
            id="2010", name="Andrew Smith", email="andrew@example.com"
        )

        MembershipFactory.create(
            person=person,
            post=self.dulwich_post,
            party=self.green_party,
            post_election=self.dulwich_post_pee,
        )

    def test_context_data(self):
        url = "/tasks/email/"

        response = self.client.get(url)
        self.assertEqual(response.context["field"], "email")
        self.assertEqual(response.context["candidates_count"], 2)
        self.assertEqual(response.context["results_count"], 1)

        self.assertContains(response, "Tessa Jowell")

    def test_template_used(self):
        response = self.client.get("/tasks/email/")
        self.assertTemplateUsed(response, "tasks/field.html")
