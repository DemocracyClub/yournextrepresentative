from candidates.tests.auth import TestUserMixin
from django.db import IntegrityError
from django.test import TestCase
from duplicates.models import DuplicateSuggestion
from people.tests.factories import PersonFactory


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
            person=self.person_1, other_person=self.person_2, user=self.user
        )

        self.assertEqual(
            DuplicateSuggestion.objects.for_person(self.person_1).count(), 1
        )
        self.assertEqual(
            DuplicateSuggestion.objects.for_person(self.person_2).count(), 1
        )

    def test_mark_as_not_duplicate(self):
        DuplicateSuggestion.objects.create(
            person=self.person_1,
            other_person=self.person_2,
            user=self.user,
            status=DuplicateSuggestion.STATUS.not_duplicate,
        )
        self.assertEqual(DuplicateSuggestion.not_duplicate.all().count(), 1)
        self.assertTrue(
            DuplicateSuggestion.objects.marked_as_not_duplicate(
                self.person_1, self.person_2
            )
        )
        self.assertTrue(
            DuplicateSuggestion.objects.marked_as_not_duplicate(
                self.person_2, self.person_1
            )
        )

    def test_not_duplicate_duplicates_create_method(self):
        """
        Make sure we can't make a duplicate duplicate suggestion using create()
        """
        DuplicateSuggestion.objects.create(
            person=self.person_1,
            other_person=self.person_2,
            user=self.user,
            status=DuplicateSuggestion.STATUS.not_duplicate,
        )
        with self.assertRaises(IntegrityError):
            DuplicateSuggestion.objects.create(
                person=self.person_2,
                other_person=self.person_1,
                user=self.user,
                status=DuplicateSuggestion.STATUS.not_duplicate,
            )

    def test_not_duplicate_duplicates_upsert(self):
        DuplicateSuggestion.objects.create(
            person=self.person_1,
            other_person=self.person_2,
            user=self.user,
            status=DuplicateSuggestion.STATUS.not_duplicate,
        )
        self.assertEqual(DuplicateSuggestion.objects.count(), 1)

        DuplicateSuggestion.objects.update_or_create(
            person=self.person_2,
            other_person=self.person_1,
            user=self.user,
            status=DuplicateSuggestion.STATUS.not_duplicate,
        )
        self.assertEqual(DuplicateSuggestion.objects.count(), 1)

        DuplicateSuggestion.objects.get_or_create(
            person=self.person_2,
            other_person=self.person_1,
            user=self.user,
            status=DuplicateSuggestion.STATUS.not_duplicate,
        )
        self.assertEqual(DuplicateSuggestion.objects.count(), 1)
