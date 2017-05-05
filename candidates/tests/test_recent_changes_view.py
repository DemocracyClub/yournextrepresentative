from __future__ import unicode_literals

from django_webtest import WebTest

from candidates.tests import factories

from .auth import TestUserMixin
from ..models import LoggedAction


class TestRecentChangesView(TestUserMixin, WebTest):

    def setUp(self):
        test_person_1 = factories.PersonExtraFactory.create(
            base__id=9876,
            base__name='Test Candidate for Recent Changes',
        )
        test_person_2 = factories.PersonExtraFactory.create(
            base__id=1234,
            base__name='Another Test Candidate for Recent Changes',
        )
        self.action1 = LoggedAction.objects.create(
            user=self.user,
            action_type='person-create',
            ip_address='127.0.0.1',
            person=test_person_1.base,
            popit_person_new_version='1234567890abcdef',
            source='Just for tests...',
        )
        self.action2 = LoggedAction.objects.create(
            user=self.user,
            action_type='candidacy-delete',
            ip_address='127.0.0.1',
            person=test_person_2.base,
            popit_person_new_version='987654321',
            source='Also just for testing',
        )
        self.response = self.app.get('/recent-changes', user=self.user_who_can_review_changes)

    def tearDown(self):
        self.action2.delete()
        self.action1.delete()

    def test_loads_all_recent_changes(self):
        tbody = self.response.html.find('tbody')
        self.assertEqual(len(tbody.find_all('tr')), 2)

    def test_allows_to_mark_a_change_as_reviewed(self):
        tbody = self.response.html.find('tbody')
        attrs = {'method': 'post', 'action': '/mark-change-as-reviewed'}
        self.assertEqual(len(tbody.find_all('form', attrs=attrs)), 2)

    def test_review_form_has_person_input(self):
        person_input = self.response.html.find_all('input', attrs={'name': 'person_id'})[0]
        self.assertEqual(person_input.get('value'), '1234')

    def test_review_form_has_logged_action_input(self):
        action_input = self.response.html.find_all('input', attrs={'name': 'logged_action_id'})[0]
        value = str(LoggedAction.objects.last().id)
        self.assertEqual(action_input.get('value'), value)

    def test_page_is_forbidden_if_user_has_no_review_permissions(self):
        response = self.app.get('/recent-changes', user=self.user, expect_errors=True)
        self.assertEqual(response.status_code, 403)
