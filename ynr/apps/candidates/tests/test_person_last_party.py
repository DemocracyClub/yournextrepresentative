from django.test import TestCase

from . import factories
from .uk_examples import UK2015ExamplesMixin

class TestPersonLastParty(UK2015ExamplesMixin, TestCase):

    def setUp(self):
        super().setUp()

    def test_both_elections(self):
        person_extra = factories.PersonExtraFactory.create(
            base__id=1234,
            base__name='John Doe',
        )
        factories.MembershipFactory.create(
            person=person_extra.base,
            post=self.dulwich_post_extra.base,
            on_behalf_of=self.labour_party_extra.base,
            post_election=self.dulwich_post_extra_pee,

        )
        factories.MembershipFactory.create(
            person=person_extra.base,
            post=self.dulwich_post_extra.base,
            on_behalf_of=self.ld_party_extra.base,
            post_election=self.dulwich_post_extra_pee_earlier,
        )
        self.assertEqual(
            person_extra.last_party(),
            self.labour_party_extra.base
        )

    def test_only_earlier(self):
        person_extra = factories.PersonExtraFactory.create(
            base__id=1234,
            base__name='John Doe',
        )
        factories.MembershipFactory.create(
            person=person_extra.base,
            post=self.dulwich_post_extra.base,
            on_behalf_of=self.ld_party_extra.base,
            post_election=self.dulwich_post_extra_pee_earlier,
        )
        self.assertEqual(
            person_extra.last_party(),
            self.ld_party_extra.base
        )

    def test_only_later(self):
        person_extra = factories.PersonExtraFactory.create(
            base__id=1234,
            base__name='John Doe',
        )
        factories.MembershipFactory.create(
            person=person_extra.base,
            post=self.dulwich_post_extra.base,
            on_behalf_of=self.labour_party_extra.base,
            post_election=self.dulwich_post_extra_pee,
        )
        self.assertEqual(
            person_extra.last_party(),
            self.labour_party_extra.base
        )
