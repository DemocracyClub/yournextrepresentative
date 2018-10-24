"""
Implements tests specific to the popolo module.
Run with "manage.py test popolo, or with python".
"""

from django.test import TestCase
from popolo.behaviors.tests.test_behaviors import (
    TimestampableTests,
    DateframeableTests,
)
from popolo.models import Organization, Post, ContactDetail
from people.models import Person
from faker import Factory
from slugify import slugify

faker = Factory.create("it_IT")  # a factory to create fake names for tests


class PersonTestCase(TimestampableTests, TestCase):
    model = Person
    object_name = "person"

    def create_instance(self, **kwargs):
        if "name" not in kwargs:
            kwargs.update({"name": u"test instance"})
        return Person.objects.create(**kwargs)

    def test_add_contact_detail(self):
        p = self.create_instance()
        p.add_contact_detail(
            contact_type=ContactDetail.CONTACT_TYPES.email, value=faker.email()
        )
        self.assertEqual(p.contact_details.count(), 1)

    def test_add_contact_details(self):
        p = self.create_instance()
        contacts = [
            {
                "contact_type": ContactDetail.CONTACT_TYPES.email,
                "value": faker.email(),
            },
            {
                "contact_type": ContactDetail.CONTACT_TYPES.phone,
                "value": faker.phone_number(),
            },
        ]
        p.add_contact_details(contacts)
        self.assertEqual(p.contact_details.count(), 2)

    def test_add_links_and_sources(self):
        p = self.create_instance()
        p.links.create(url="http://link.example.org/", note="Note")
        p.sources.create(url="http://source.example.org/", note="Source note")
        self.assertEqual(p.links.count(), 1)
        self.assertEqual(
            p.sources.filter(url="http://link.example.org/").count(), 0
        )


class OrganizationTestCase(DateframeableTests, TimestampableTests, TestCase):
    model = Organization
    object_name = "organization"

    def create_instance(self, **kwargs):
        if "name" not in kwargs:
            kwargs.update({"name": u"test instance"})
        kwargs["slug"] = slugify("-".join([v for k, v in kwargs.items()]))
        return Organization.objects.create(**kwargs)

    def test_add_post(self):
        o = Organization.objects.create(name=faker.company())
        o.add_post(label=u"CEO")
        self.assertEqual(o.posts.count(), 1)

    def test_add_posts(self):
        o = Organization.objects.create(name=faker.company())
        o.add_posts([{"label": u"Presidente"}, {"label": u"Vicepresidente"}])
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
