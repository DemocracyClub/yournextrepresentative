from django.test import TestCase

from . import factories
from .uk_examples import UK2015ExamplesMixin


class TestPersonLastParty(UK2015ExamplesMixin, TestCase):
    def setUp(self):
        super().setUp()

    def test_both_elections(self):
        person = factories.PersonFactory.create(id=1234, name="John Doe")
        factories.MembershipFactory.create(
            person=person,
            post=self.dulwich_post,
            party=self.labour_party,
            post_election=self.dulwich_post_pee,
        )
        factories.MembershipFactory.create(
            person=person,
            post=self.dulwich_post,
            party=self.ld_party,
            post_election=self.dulwich_post_pee_earlier,
        )
        self.assertEqual(person.last_party(), self.labour_party)

    def test_only_earlier(self):
        person = factories.PersonFactory.create(id=1234, name="John Doe")
        factories.MembershipFactory.create(
            person=person,
            post=self.dulwich_post,
            party=self.ld_party,
            post_election=self.dulwich_post_pee_earlier,
        )
        self.assertEqual(person.last_party(), self.ld_party)

    def test_only_later(self):
        person = factories.PersonFactory.create(id=1234, name="John Doe")
        factories.MembershipFactory.create(
            person=person,
            post=self.dulwich_post,
            party=self.labour_party,
            post_election=self.dulwich_post_pee,
        )
        self.assertEqual(person.last_party(), self.labour_party)
