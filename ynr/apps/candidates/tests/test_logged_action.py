import people.tests.factories
from candidates.models import LoggedAction
from candidates.models.db import ActionType
from django.test import TestCase

from .auth import TestUserMixin
from .uk_examples import UK2015ExamplesMixin


class TestLoggedAction(TestUserMixin, UK2015ExamplesMixin, TestCase):
    def test_logged_action_repr(self):
        person = people.tests.factories.PersonFactory.create(
            id="9876", name="Test Candidate"
        )
        action = LoggedAction.objects.create(
            user=self.user,
            action_type=ActionType.PERSON_CREATE,
            ip_address="127.0.0.1",
            person=person,
            popit_person_new_version="1234567890abcdef",
            source="Just for tests...",
        )
        self.assertEqual(
            repr(action),
            str("<LoggedAction: username='john' action_type='person-create'>"),
        )

    def test_subject_person(self):
        person = people.tests.factories.PersonFactory.create(
            id="9876", name="Test Candidate"
        )
        action = LoggedAction.objects.create(
            user=self.user,
            action_type=ActionType.PERSON_CREATE,
            ip_address="127.0.0.1",
            person=person,
            popit_person_new_version="1234567890abcdef",
            source="Just for tests...",
        )
        self.assertEqual(
            action.subject_html,
            '<a href="/person/9876">Test Candidate (9876)</a>',
        )

    def test_subject_ballot(self):
        action = LoggedAction.objects.create(
            user=self.user,
            action_type=ActionType.CONSTITUENCY_LOCK,
            ip_address="127.0.0.1",
            post=self.camberwell_post,
            ballot=self.camberwell_post_ballot,
            popit_person_new_version="1234567890abcdef",
            source="Just for tests...",
        )
        self.assertEqual(
            action.subject_html,
            '<a href="/elections/parl.65913.2015-05-07/">Camberwell and Peckham (65913)</a>',
        )
