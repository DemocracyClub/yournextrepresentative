"""
Implements tests specific to the popolo module.
Run with "manage.py test popolo, or with python".
"""

from unittest.mock import PropertyMock, patch
from django.test import TestCase
from faker import Factory
from slugify import slugify
from candidates.models.popolo_extra import Ballot

from people.models import Person
from popolo.behaviors.tests.test_behaviors import DateframeableTests
from popolo.models import Membership, Organization

faker = Factory.create("it_IT")  # a factory to create fake names for tests


class PersonTestCase(TestCase):
    model = Person
    object_name = "person"

    def create_instance(self, **kwargs):
        if "name" not in kwargs:
            kwargs.update({"name": u"test instance"})
        return Person.objects.create(**kwargs)


class OrganizationTestCase(DateframeableTests, TestCase):
    model = Organization
    object_name = "organization"

    def create_instance(self, **kwargs):
        if "name" not in kwargs:
            kwargs.update({"name": u"test instance"})
        kwargs["slug"] = slugify("-".join([v for k, v in kwargs.items()]))
        return Organization.objects.create(**kwargs)

    def test_add_post(self):
        o = Organization.objects.create(name=faker.company())
        o.add_post(label=u"CEO", identifier="123")
        self.assertEqual(o.posts.count(), 1)

    def test_add_posts(self):
        o = Organization.objects.create(name=faker.company())
        o.add_posts(
            [
                {"label": u"Presidente", "identifier": 123},
                {"label": u"Vicepresidente", "identifier": 456},
            ]
        )
        self.assertEqual(o.posts.count(), 2)

    def test_it_copies_the_foundation_date_to_start_date(self):
        o = Organization(name=faker.company(), founding_date=faker.year())
        # it is not set to start_date until saved
        self.assertIsNone(o.start_date)
        o.save()
        self.assertEqual(o.start_date, o.founding_date)

    def test_it_copies_the_dissolution_date_to_end_date(self):
        o = Organization(name=faker.company(), dissolution_date=faker.year())
        # it is not set to start_date until saved
        self.assertIsNone(o.end_date)
        o.save()
        self.assertEqual(o.end_date, o.dissolution_date)


class TestMembership(TestCase):
    def test_is_welsh_run_ballot(self):
        """
        Test that when a the Ballot.is_welsh_run returns True or False, the
        Membership.is_welsh_run_ballot returns the same
        """
        for case in [True, False]:
            with self.subTest(msg=case):
                with patch.object(
                    Ballot, "is_welsh_run", new_callable=PropertyMock
                ) as mock:
                    mock.return_value = case
                    membership = Membership(ballot=Ballot())
                    assert membership.is_welsh_run_ballot is case
                    mock.assert_called_once()
