from django.test import TestCase

import people.tests.factories
from people.models import Person

from .auth import TestUserMixin
from .uk_examples import UK2015ExamplesMixin
from . import factories


class TestMissingFields(TestUserMixin, UK2015ExamplesMixin, TestCase):
    def setUp(self):
        super().setUp()
        person_old_election = people.tests.factories.PersonFactory.create(
            id=100, name="John Past"
        )
        person_no_details = people.tests.factories.PersonFactory.create(
            id=101, name="Jane Doe"
        )
        person_empty_slogan = people.tests.factories.PersonFactory.create(
            id=102, name="John Smith", birth_date="1999-12-31"
        )
        person_empty_slogan.tmp_person_identifiers.create(
            value_type="twitter_username", value="anothermadeuptwitterusername"
        )

        person_with_details = people.tests.factories.PersonFactory.create(
            id=103, name="Joe Bloggs", birth_date="1980-01-01"
        )
        person_with_details.tmp_person_identifiers.create(
            value_type="twitter_username", value="madeuptwitterusername"
        )

        factories.MembershipFactory.create(
            person=person_old_election,
            post=self.dulwich_post,
            party=self.labour_party,
            post_election=self.dulwich_post_ballot_earlier,
        )
        factories.MembershipFactory.create(
            person=person_no_details,
            post=self.dulwich_post,
            party=self.labour_party,
            post_election=self.dulwich_post_ballot,
        )
        factories.MembershipFactory.create(
            person=person_empty_slogan,
            post=self.dulwich_post,
            party=self.labour_party,
            post_election=self.dulwich_post_ballot,
        )
        factories.MembershipFactory.create(
            person=person_with_details,
            post=self.dulwich_post,
            party=self.green_party,
            post_election=self.dulwich_post_ballot,
        )

    def test_find_those_missing_dob(self):
        qs = Person.objects.missing("birth_date")
        self.assertEqual(qs.count(), 1)
        self.assertEqual(qs[0].name, "Jane Doe")

    def test_find_those_missing_twitter(self):
        qs = Person.objects.missing("twitter_username")
        self.assertEqual(qs.count(), 1)
        self.assertEqual(qs[0].name, "Jane Doe")

    def test_non_existent_field(self):
        with self.assertRaises(ValueError):
            Person.objects.missing("quux")
