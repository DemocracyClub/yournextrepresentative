from django_webtest import WebTest

from candidates.tests.uk_examples import UK2015ExamplesMixin
from candidates.tests.auth import TestUserMixin
from candidates.models import LoggedAction
from people.tests.factories import PersonFactory

from people.merging import PersonMerger
from people.models import Person, PersonImage


class TestMerging(TestUserMixin, UK2015ExamplesMixin, WebTest):
    def test_person_merging(self):
        """
        A small interface / smoke test for the PersonMerger class
        """
        dest_person = PersonFactory()
        source_person = PersonFactory()
        LoggedAction.objects.create(person=source_person, user=self.user)
        LoggedAction.objects.create(person=dest_person, user=self.user)

        self.assertEqual(Person.objects.count(), 2)
        self.assertEqual(LoggedAction.objects.count(), 2)

        merger = PersonMerger(dest_person, source_person)
        merger.merge()

        self.assertEqual(Person.objects.count(), 1)
        self.assertEqual(LoggedAction.objects.count(), 2)
