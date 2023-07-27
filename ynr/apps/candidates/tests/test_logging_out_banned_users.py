from candidates.tests.uk_examples import UK2015ExamplesMixin
from django_webtest import WebTest

from .auth import TestUserMixin


class TestLoggingOutMiddleware(TestUserMixin, UK2015ExamplesMixin, WebTest):
    def test_no_logout_if_is_active(self):
        self.app.get("/", user=self.user)
        response = self.app.get("/")
        self.assertIn("Sign out", response.text)

    def test_logout_after_set_inactive(self):
        self.app.get("/", user=self.user)
        self.user.is_active = False
        self.user.save()
        response = self.app.get("/")
        self.assertIn("Sign in to edit", response.text)
