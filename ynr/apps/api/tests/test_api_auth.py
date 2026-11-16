from candidates.tests.auth import TestUserMixin
from django.test import TestCase
from rest_framework.authtoken.models import Token

PROTECTED_URLS = [
    "/api/next/",
    "/api/next/people/",
    "/api/v0.9/",
    "/api/v0.9/persons/",
]


class TestAPIAuth(TestUserMixin, TestCase):
    def setUp(self):
        super().setUp()
        self.token = Token.objects.get(user=self.user)

    def _token_header(self, key=None):
        return {"HTTP_AUTHORIZATION": f"Token {key or self.token.key}"}

    def test_anonymous_requests_are_rejected(self):
        for url in PROTECTED_URLS:
            with self.subTest(url=url):
                response = self.client.get(url)
                self.assertEqual(response.status_code, 401)
                self.assertEqual(response["WWW-Authenticate"], "Token")

    def test_token_in_header(self):
        for url in PROTECTED_URLS:
            with self.subTest(url=url):
                response = self.client.get(url, **self._token_header())
                self.assertEqual(response.status_code, 200)

    def test_token_in_query_string(self):
        for url in PROTECTED_URLS:
            with self.subTest(url=url):
                response = self.client.get(url, {"auth_token": self.token.key})
                self.assertEqual(response.status_code, 200)

    def test_header_takes_precedence_over_query_string(self):
        response = self.client.get(
            "/api/next/people/",
            {"auth_token": "not-a-real-token"},
            **self._token_header(),
        )
        self.assertEqual(response.status_code, 200)

    def test_invalid_token_is_rejected(self):
        response = self.client.get(
            "/api/next/people/", **self._token_header("not-a-real-token")
        )
        self.assertEqual(response.status_code, 401)
        response = self.client.get(
            "/api/next/people/", {"auth_token": "not-a-real-token"}
        )
        self.assertEqual(response.status_code, 401)

    def test_inactive_user_token_is_rejected(self):
        self.user.is_active = False
        self.user.save()
        response = self.client.get("/api/next/people/", **self._token_header())
        self.assertEqual(response.status_code, 401)

    def test_session_auth(self):
        self.client.force_login(self.user)
        for url in PROTECTED_URLS:
            with self.subTest(url=url):
                response = self.client.get(url)
                self.assertEqual(response.status_code, 200)

    def test_session_auth_browsable_api(self):
        self.client.force_login(self.user)
        response = self.client.get("/api/next/people/", HTTP_ACCEPT="text/html")
        self.assertEqual(response.status_code, 200)
        self.assertIn("text/html", response["Content-Type"])

    def test_unsafe_methods_are_forbidden(self):
        for method in ("post", "put", "patch", "delete"):
            with self.subTest(method=method, auth="token"):
                response = getattr(self.client, method)(
                    "/api/next/people/", **self._token_header()
                )
                self.assertEqual(response.status_code, 403)
        self.client.force_login(self.user)
        for method in ("post", "put", "patch", "delete"):
            with self.subTest(method=method, auth="session"):
                response = getattr(self.client, method)("/api/next/people/")
                self.assertEqual(response.status_code, 403)

    def test_docs_and_redirect_are_public(self):
        response = self.client.get("/api/")
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response["Location"], "/api/docs/")
        for url in ("/api/docs/", "/api/docs/terms/", "/api/docs/next/"):
            with self.subTest(url=url):
                response = self.client.get(url)
                self.assertEqual(response.status_code, 200)

    def test_no_anonymous_cache_headers(self):
        for kwargs in ({}, self._token_header()):
            response = self.client.get("/api/next/people/", **kwargs)
            self.assertNotIn("max-age=3600", response.get("Cache-Control", ""))

    def test_no_rate_limit(self):
        for _ in range(15):
            response = self.client.get("/api/next/", **self._token_header())
            self.assertEqual(response.status_code, 200)
