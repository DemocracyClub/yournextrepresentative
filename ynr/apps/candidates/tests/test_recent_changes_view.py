from django_webtest import WebTest

import people.tests.factories
from candidates.models import LoggedAction
from candidates.models.db import ActionType


from .auth import TestUserMixin


class TestRecentChangesView(TestUserMixin, WebTest):
    def setUp(self):
        test_person_1 = people.tests.factories.PersonFactory.create(
            id=9876, name="Test Candidate for Recent Changes"
        )
        test_person_2 = people.tests.factories.PersonFactory.create(
            id=1234, name="Another Test Candidate for Recent Changes"
        )
        self.action1 = LoggedAction.objects.create(
            user=self.user,
            action_type=ActionType.PERSON_CREATE,
            ip_address="127.0.0.1",
            person=test_person_1,
            popit_person_new_version="1234567890abcdef",
            source="Just for tests...",
        )
        self.action2 = LoggedAction.objects.create(
            user=self.user,
            action_type=ActionType.CANDIDACY_DELETE,
            ip_address="127.0.0.1",
            person=test_person_2,
            popit_person_new_version="987654321",
            source="Also just for testing",
        )

    def tearDown(self):
        self.action2.delete()
        self.action1.delete()

    def test_recent_changes_page(self):
        # Just a smoke test to check that the page loads:
        response = self.app.get("/recent-changes")
        table = response.html.find("table")
        self.assertEqual(3, len(table.find_all("tr")))
