from django.test import TestCase

from candidates.tests.auth import TestUserMixin
from duplicates import merge_helpers
from duplicates.models import DuplicateSuggestion
from people.tests.factories import PersonFactory


class TestMergeHelper(TestUserMixin, TestCase):
    def test_merge_deletes_duplicate(self):
        # Make sure we have no DuplicateSuggestion
        self.assertFalse(DuplicateSuggestion.objects.all().exists())

        # Make some people
        p1, p2, p3 = PersonFactory.create_batch(3)

        # suggest they're the same
        ds = DuplicateSuggestion.objects.create(
            person=p2, other_person=p1, user=self.user
        )

        # suggest someone else is the same
        ds = DuplicateSuggestion.objects.create(
            person=p1, other_person=p3, user=self.user
        )

        # Pretend we've merged p2 in to p1
        # Then call the merge helper
        merge_helpers.alter_duplicate_suggestion_post_merge(p1, p2)

        # Merging these two should have deleted ds
        self.assertEqual(DuplicateSuggestion.objects.all().count(), 1)

    def test_merge_moves_person_id_to_primary(self):
        # Make sure we have no DuplicateSuggestion
        self.assertFalse(DuplicateSuggestion.objects.all().exists())

        # Make some people
        p1, p2, p3 = PersonFactory.create_batch(3)

        # We're going to merge p1 in to p2
        # but someone things p3 is a dupe of p2
        ds = DuplicateSuggestion.objects.create(
            person=p2, other_person=p3, user=self.user
        )
        self.assertEqual(DuplicateSuggestion.objects.first().person, p2)
        self.assertEqual(DuplicateSuggestion.objects.first().other_person, p3)

        # Pretend we've merged p2 in to p1
        # Then call the merge helper
        merge_helpers.alter_duplicate_suggestion_post_merge(p1, p2)

        # Check that the DS is now between p1 and p3
        self.assertEqual(DuplicateSuggestion.objects.all().count(), 1)
        ds = DuplicateSuggestion.objects.first()
        self.assertEqual(ds.person, p1)
        self.assertEqual(ds.other_person, p3)
