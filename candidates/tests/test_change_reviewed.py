from django.test import TestCase

from candidates.models import ChangeReviewed


class TestChangeReviewed(TestCase):
    def test_requires_a_popolo_person(self):
        with self.assertRaises(ValueError):
            ChangeReviewed.objects.create(
                person=None,
                logged_action=1,
                reviewer=1
            )

    def test_requires_a_logged_action(self):
        with self.assertRaises(ValueError):
            ChangeReviewed.objects.create(
                person=1,
                logged_action=None,
                reviewer=1
            )

    def test_requires_a_reviewer(self):
        with self.assertRaises(ValueError):
            ChangeReviewed.objects.create(
                person=1,
                logged_action=1,
                reviewer=None
            )
