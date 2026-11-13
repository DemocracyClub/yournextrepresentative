from candidates.tests.auth import TestUserMixin
from candidates.tests.uk_examples import UK2015ExamplesMixin
from django.urls import reverse
from django_webtest import WebTest


class TestAPI(TestUserMixin, UK2015ExamplesMixin, WebTest):
    def setUp(self):
        super().setUp()
        self.app.set_user(self.user)

    def test_docs_html(self):
        """
        Check that the API docs are being rendered as Markdown
        """
        resp = self.app.get(reverse("api-home"), user=None)
        self.assertContains(resp, "<h3>Usage terms</h3>")

    def test_docs_curl_example_uses_request_host(self):
        self.client.force_login(self.user)
        resp = self.client.get(
            reverse("api-home"), HTTP_HOST="candidates.democracyclub.org.uk"
        )
        self.assertContains(
            resp,
            "curl http://candidates.democracyclub.org.uk/api/next/ "
            f"-H 'Authorization: Token {self.user.auth_token.key}'",
        )

    def test_docs_reject_malformed_host(self):
        self.client.force_login(self.user)
        resp = self.client.get(
            reverse("api-home"), HTTP_HOST='evil.example"><script>'
        )
        self.assertEqual(resp.status_code, 400)

    def test_each_endpoint(self):
        """
        TODO: Convert to use pytest-subtest

        :return:
        """
        endpoints_to_ignore = ["candidates_for_postcode"]
        for version in ("v0.9", "next"):
            response = self.app.get("/api/{}/".format(version))
            for name, url in response.json.items():
                # This slightly odd dance is needed because
                # pytest doesn't actually support subtests yet
                # (see https://github.com/pytest-dev/pytest/issues/1367)
                # Use try/except/failureException to log the endpoint that
                # failed. Unlike proper subtests, this will fail the test,
                # but hopefully writing it like this will mean it starts working
                # if/when pytest supports subtests properly
                if name in endpoints_to_ignore:
                    # Ignore some endpoints as they require more than a simple
                    # request and check for 200
                    continue
                with self.subTest(name, url=url):
                    response = self.app.get(url, expect_errors=True)
                    try:
                        self.assertEqual(response.status_code, 200)
                    except AssertionError:
                        raise self.failureException(
                            "Error with '{}' {} endpoint".format(version, name)
                        )
