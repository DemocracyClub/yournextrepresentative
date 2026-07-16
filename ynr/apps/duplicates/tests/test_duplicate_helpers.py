from candidates.tests.auth import TestUserMixin
from django.test import TestCase
from duplicates.helpers import get_previous_rejections
from duplicates.models import DuplicateSuggestion
from people.tests.factories import PersonFactory


class TestGetPreviousRejections(TestUserMixin, TestCase):
    def setUp(self):
        # Sort by pk so p1.pk < p2.pk < p3.pk is guaranteed throughout.
        self.p1, self.p2, self.p3 = sorted(
            PersonFactory.create_batch(3), key=lambda p: p.pk
        )

    def _make_rejection(self, person, other_person, reasoning=""):
        return DuplicateSuggestion.objects.create(
            person=person,
            other_person=other_person,
            user=self.user,
            status=DuplicateSuggestion.STATUS.not_duplicate,
            rejection_reasoning=reasoning,
        )

    def test_empty_pairs_returns_empty_dict(self):
        result = get_previous_rejections([])
        self.assertEqual(result, {})

    def test_pair_with_no_rejections_returns_empty_list(self):
        result = get_previous_rejections([(self.p1.pk, self.p2.pk)])
        self.assertEqual(result[(self.p1.pk, self.p2.pk)], [])

    def test_single_rejection_is_returned(self):
        rejection = self._make_rejection(self.p1, self.p2)
        result = get_previous_rejections([(self.p1.pk, self.p2.pk)])
        self.assertEqual(result[(self.p1.pk, self.p2.pk)], [rejection])

    def test_open_suggestions_are_excluded(self):
        DuplicateSuggestion.objects.create(
            person=self.p1, other_person=self.p2, user=self.user
        )
        result = get_previous_rejections([(self.p1.pk, self.p2.pk)])
        self.assertEqual(result[(self.p1.pk, self.p2.pk)], [])

    def test_multiple_rejections_all_returned(self):
        r1 = self._make_rejection(self.p1, self.p2, "first reason")
        r2 = self._make_rejection(self.p1, self.p2, "second reason")
        result = get_previous_rejections([(self.p1.pk, self.p2.pk)])
        self.assertCountEqual(result[(self.p1.pk, self.p2.pk)], [r1, r2])

    def test_pairs_work_with_low_id_first(self):
        rejection = self._make_rejection(self.p1, self.p2)
        result = get_previous_rejections([(self.p1.pk, self.p2.pk)])
        self.assertEqual(result[(self.p1.pk, self.p2.pk)], [rejection])

    def test_multiple_pairs_rejections_correctly_separated(self):
        r12 = self._make_rejection(self.p1, self.p2)
        r13 = self._make_rejection(self.p1, self.p3)
        result = get_previous_rejections(
            [(self.p1.pk, self.p2.pk), (self.p1.pk, self.p3.pk)]
        )
        self.assertEqual(result[(self.p1.pk, self.p2.pk)], [r12])
        self.assertEqual(result[(self.p1.pk, self.p3.pk)], [r13])

    def test_rejections_for_other_pairs_not_included(self):
        self._make_rejection(self.p1, self.p3)
        result = get_previous_rejections([(self.p1.pk, self.p2.pk)])
        self.assertEqual(result[(self.p1.pk, self.p2.pk)], [])

    def test_pairs_with_high_id_first(self):
        # p2.pk > p1.pk - the pair is passed reversed relative to DB storage
        # It is expected that this will not match anything
        self._make_rejection(self.p1, self.p2)
        result = get_previous_rejections([(self.p2.pk, self.p1.pk)])
        self.assertEqual(result[(self.p2.pk, self.p1.pk)], [])
