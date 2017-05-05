from __future__ import unicode_literals

from django.core.exceptions import ValidationError
from django_webtest import WebTest

from .auth import TestUserMixin
from ..models import ChangeReviewed, LoggedAction
from candidates.tests import factories

from popolo.models import Person


class TestMarkChangeAsReviewedView(TestUserMixin, WebTest):
    def setUp(self):
        test_person_1 = factories.PersonExtraFactory.create(
            base__id=9876,
            base__name='Test Candidate for Recent Changes',
        )
        self.action1 = LoggedAction.objects.create(
            user=self.user,
            action_type='person-create',
            ip_address='127.0.0.1',
            person=test_person_1.base,
            popit_person_new_version='1234567890abcdef',
            source='Just for tests...',
        )
        self.app.get('/recent-changes', user=self.user_who_can_review_changes)

    def test_redirects_to_recent_changes_page(self):
        response = self.post_to_change_reviewed(
            Person.objects.last().id,
            LoggedAction.objects.last().id,
        )
        self.assertEqual(response.status_code, 302)

    def test_marks_a_change_as_reviewed(self):
        count_before = len(ChangeReviewed.objects.all())
        self.post_to_change_reviewed(
            Person.objects.last().id,
            LoggedAction.objects.last().id,
        )
        count_after = len(ChangeReviewed.objects.all())
        self.assertEqual(count_after - count_before, 1)

    def test_404s_if_person_not_in_database(self):
        response = self.post_to_change_reviewed(
            0,
            LoggedAction.objects.last().id,
        )
        self.assertEqual(response.status_code, 404)

    def test_404s_if_logged_action_not_in_database(self):
        response = self.post_to_change_reviewed(
            Person.objects.last().id,
            0,
        )
        self.assertEqual(response.status_code, 404)

    def test_errors_if_person_field_present_but_empty(self):
        with self.assertRaises(ValidationError):
            self.post_to_change_reviewed(
                '',
                LoggedAction.objects.last().id,
            )

    def test_errors_if_logged_action_field_present_but_empty(self):
        with self.assertRaises(ValidationError):
            self.post_to_change_reviewed(
                Person.objects.last().id,
                '',
            )

    def test_errors_if_person_field_not_present(self):
        with self.assertRaises(ValidationError):
            self.app.post(
                '/mark-change-as-reviewed',
                {
                    'csrfmiddlewaretoken': self.app.cookies['csrftoken'],
                    'logged_action_id': LoggedAction.objects.last().id,
                },
                user=self.user_who_can_review_changes,
            )

    def test_errors_if_logged_action_field_not_present(self):
        with self.assertRaises(ValidationError):
            self.app.post(
                '/mark-change-as-reviewed',
                {
                    'csrfmiddlewaretoken': self.app.cookies['csrftoken'],
                    'person_id': Person.objects.last().id,
                },
                user=self.user_who_can_review_changes,
            )

    def test_forbids_access_if_reviewer_has_no_review_permissions(self):
        response = self.post_to_change_reviewed(
            Person.objects.last().id,
            LoggedAction.objects.last().id,
            self.user
        )
        self.assertEqual(response.status_code, 403)

    def post_to_change_reviewed(self, person_id, logged_action_id, user=None):
        return self.app.post(
            '/mark-change-as-reviewed',
            {
                'csrfmiddlewaretoken': self.app.cookies['csrftoken'],
                'person_id': person_id,
                'logged_action_id': logged_action_id,
            },
            user=user or self.user_who_can_review_changes,
            expect_errors=True,
        )
