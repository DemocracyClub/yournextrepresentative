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
        DuplicateSuggestion.objects.create(
            person=p2, other_person=p1, user=self.user
        )

        # suggest someone else is the same
        DuplicateSuggestion.objects.create(
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
        merge_helpers.alter_duplicate_suggestion_post_merge(
            source_person=p2, dest_person=p1
        )

        # Check that the DS is now between p1 and p3
        self.assertEqual(DuplicateSuggestion.objects.all().count(), 1)
        ds = DuplicateSuggestion.objects.first()
        self.assertEqual(ds.person, p1)
        self.assertEqual(ds.other_person, p3)

    def test_order_is_correct_after_updating_suggestions(self):
        """
        Tests situation where there are two duplicates involving same person,
        and that the resulting suggestions are ordered correctly
        """
        self.assertFalse(DuplicateSuggestion.objects.all().exists())

        person1 = PersonFactory(pk=1)
        person2 = PersonFactory(pk=2)
        person3 = PersonFactory(pk=3)

        # merging would make person 3 person 1
        ds1 = DuplicateSuggestion.objects.create(
            person=person3, other_person=person1, user=self.user
        )

        # merging would make person 3 person 2
        ds2 = DuplicateSuggestion.objects.create(
            person=person2, other_person=person3, user=self.user
        )
        self.assertEqual(DuplicateSuggestion.objects.all().count(), 2)

        # check the orders are correct - the 'person' PK should be lower than
        # 'other_person'
        assert ds1.person.pk == 1
        assert ds1.other_person.pk == 3
        assert ds2.person.pk == 2
        assert ds2.other_person.pk == 3

        # merge 3 in to 1
        merge_helpers.alter_duplicate_suggestion_post_merge(
            source_person=ds1.other_person, dest_person=ds1.person
        )

        ds2.refresh_from_db()

        # originally person2 was the destination "person" as they had the lower
        # ID - but now that person 3 has been merged to person 1, this should
        # make person2 the source "other_person"
        self.assertEqual(DuplicateSuggestion.objects.all().count(), 1)
        assert ds2.person.pk == 1
        assert ds2.other_person.pk == 2
