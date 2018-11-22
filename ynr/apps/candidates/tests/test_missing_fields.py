from django.test import TestCase

import people.tests.factories
from candidates.models import ExtraField
from people.models import Person

from .auth import TestUserMixin
from .uk_examples import UK2015ExamplesMixin
from . import factories


class TestMissingFields(TestUserMixin, UK2015ExamplesMixin, TestCase):
    def setUp(self):
        super().setUp()
        slogan_field = ExtraField.objects.create(key="slogan", type="line")
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
        person_empty_slogan.extra_field_values.create(
            field=slogan_field, value=""
        )
        person_with_details = people.tests.factories.PersonFactory.create(
            id=103, name="Joe Bloggs", birth_date="1980-01-01"
        )
        person_with_details.tmp_person_identifiers.create(
            value_type="twitter_username", value="madeuptwitterusername"
        )
        person_with_details.extra_field_values.create(
            field=slogan_field, value="Things can only get better"
        )
        factories.MembershipFactory.create(
            person=person_old_election,
            post=self.dulwich_post,
            party=self.labour_party,
            post_election=self.dulwich_post_pee_earlier,
        )
        factories.MembershipFactory.create(
            person=person_no_details,
            post=self.dulwich_post,
            party=self.labour_party,
            post_election=self.dulwich_post_pee,
        )
        factories.MembershipFactory.create(
            person=person_empty_slogan,
            post=self.dulwich_post,
            party=self.labour_party,
            post_election=self.dulwich_post_pee,
        )
        factories.MembershipFactory.create(
            person=person_with_details,
            post=self.dulwich_post,
            party=self.green_party,
            post_election=self.dulwich_post_pee,
        )

    def test_find_those_missing_dob(self):
        qs = Person.objects.missing("birth_date")
        self.assertEqual(qs.count(), 1)
        self.assertEqual(qs[0].name, "Jane Doe")

    def test_find_those_missing_twitter(self):
        qs = Person.objects.missing("twitter_username")
        self.assertEqual(qs.count(), 1)
        self.assertEqual(qs[0].name, "Jane Doe")

    def test_find_those_missing_slogan(self):
        qs = Person.objects.missing("slogan").order_by("name")
        self.assertEqual(qs.count(), 2)
        self.assertEqual(qs[0].name, "Jane Doe")
        self.assertEqual(qs[1].name, "John Smith")

    def test_non_existent_field(self):
        with self.assertRaises(ValueError):
            Person.objects.missing("quux")
