import time
from datetime import timedelta

from candidates.middleware import RollingSessionExpiryMiddleware
from django.contrib.auth.models import User
from django.contrib.sessions.models import Session
from django.test import TestCase
from django.utils import timezone


class TestRollingSessionExpiryMiddleware(TestCase):
    url = "/status_check/"

    def setUp(self):
        self.user = User.objects.create_user(
            "jane", "jane@example.com", "notagoodpassword"
        )
        self.client.force_login(self.user)
        self.session_key = self.client.session.session_key
        # The first request after signing in stamps the session, so get that
        # out of the way before each test sets up the state it cares about.
        self.client.get(self.url)

    def get_expire_date(self):
        return Session.objects.get(session_key=self.session_key).expire_date

    def set_expire_date(self, expire_date):
        Session.objects.filter(session_key=self.session_key).update(
            expire_date=expire_date
        )

    def set_extended_at(self, extended_at):
        session = self.client.session
        session[RollingSessionExpiryMiddleware.SESSION_KEY] = extended_at
        session.save()

    def test_not_extended_within_a_day(self):
        five_days_away = timezone.now() + timedelta(days=5)
        self.set_expire_date(five_days_away)

        self.client.get(self.url)

        self.assertEqual(self.get_expire_date(), five_days_away)

    def test_extended_after_a_day(self):
        self.set_extended_at(time.time() - timedelta(days=2).total_seconds())
        self.set_expire_date(timezone.now() + timedelta(days=5))

        self.client.get(self.url)

        self.assertGreater(
            self.get_expire_date(), timezone.now() + timedelta(days=13)
        )

    def test_repeated_requests_only_extend_once(self):
        self.set_extended_at(time.time() - timedelta(days=2).total_seconds())

        self.client.get(self.url)
        extended = self.get_expire_date()
        self.client.get(self.url)

        self.assertEqual(self.get_expire_date(), extended)

    def test_anonymous_users_get_no_session(self):
        self.client.logout()

        self.client.get(self.url)

        self.assertFalse(Session.objects.exists())
