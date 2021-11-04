from django.test import TestCase

from candidates.tests.factories import PersonFactory
from candidates.tests.auth import TestUserMixin
from duplicates.models import DuplicateSuggestion


class TestDuplicateSuggestion(TestUserMixin, TestCase):
    def setUp(self):
        self.people = PersonFactory.create_batch(10)
        self.person_1 = self.people[0]
        self.person_2 = self.people[1]


    def test_queryset_finds_bidirectional_duplicates(self):
        """
        Test that the `for_person` queryset finds duplicates in each direction.
        """
        DuplicateSuggestion.objects.create(
            person=self.person_1,
            other_person=self.person_2,
            user=self.user,
        )

        self.assertEqual(
            DuplicateSuggestion.objects.for_person(self.person_1).count(),
            1
        )
        self.assertEqual(
            DuplicateSuggestion.objects.for_person(self.person_2).count(),
            1
        )

    def test_mark_as_not_duplicate(self):
        DuplicateSuggestion.objects.create(
            person=self.person_1,
            other_person=self.person_2,
            user=self.user,
            status=DuplicateSuggestion.STATUS.not_duplicate
        )
        self.assertEqual(
            DuplicateSuggestion.not_duplicate.all().count(),
            1
        )
        self.assertTrue(
            DuplicateSuggestion.objects.marked_as_not_duplicate(
                self.person_1, self.person_2)
        )
        self.assertTrue(
            DuplicateSuggestion.objects.marked_as_not_duplicate(
                self.person_2, self.person_1)
        )

