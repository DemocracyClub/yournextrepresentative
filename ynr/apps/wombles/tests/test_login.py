from django.contrib.auth.models import User
from django.core import mail
from django.urls import reverse
from django_webtest import WebTest
from sesame.utils import get_query_string


class TestWombleLogin(WebTest):
    def test_email_sent(self):
        response = self.app.get(reverse("wombles:login"))
        csrftoken = self.app.cookies["csrftoken"]
        response = self.app.post(
            reverse("wombles:login"),
            params={
                "csrfmiddlewaretoken": csrftoken,
                "email": "test1@example.com",
            },
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(
            mail.outbox[0].subject,
            "Your magic link to log in to the Democracy Club Candidates site",
        )

    def test_login(self):
        response = self.app.get(reverse("wombles:login"))
        csrftoken = self.app.cookies["csrftoken"]
        response = self.app.post(
            reverse("wombles:login"),
            params={
                "csrfmiddlewaretoken": csrftoken,
                "email": "test1@example.com",
            },
        )

        user = User.objects.get(email="test1@example.com")
        querystring = get_query_string(user=user)

        response = (
            self.app.get(reverse("wombles:authenticate") + querystring)
            .follow()
            .follow()
        )
        self.assertTrue(response.context["user"].is_authenticated)
        self.assertEqual(response.context["request"].path, "/accounts/details")

    def test_login_twice(self):
        response = self.app.get(reverse("wombles:login"))
        csrftoken = self.app.cookies["csrftoken"]
        response = self.app.post(
            reverse("wombles:login"),
            params={
                "csrfmiddlewaretoken": csrftoken,
                "email": "test1@example.com",
            },
        )

        user = User.objects.get(email="test1@example.com")
        querystring = get_query_string(user=user)

        self.app.get(reverse("wombles:authenticate") + querystring).follow()

        self.app.get(reverse("wombles:login"))
        csrftoken = self.app.cookies["csrftoken"]
        response = self.app.post(
            reverse("wombles:login"),
            params={
                "csrfmiddlewaretoken": csrftoken,
                "email": "test1@example.com",
            },
        ).follow()
        self.assertEqual(response.status_code, 200)

        user = User.objects.get(email="test1@example.com")
        querystring = get_query_string(user=user)

        response = self.app.get(
            reverse("wombles:authenticate") + querystring
        ).follow()
        self.assertEqual(response.status_code, 200)

        self.assertTrue(response.context["user"].is_authenticated)

    def test_create_with_no_username(self):
        User.objects.create(email="test1@example.com", username="Example1")
        self.assertEqual(User.objects.count(), 1)

        response = self.app.get(reverse("wombles:login"))
        csrftoken = self.app.cookies["csrftoken"]
        response = self.app.post(
            reverse("wombles:login"),
            params={
                "csrfmiddlewaretoken": csrftoken,
                "email": "test1@example.com",
            },
        ).follow()

        self.assertEqual(response.status_code, 200)
        self.assertEqual(User.objects.count(), 1)

        self.app.get(reverse("wombles:login"))
        csrftoken = self.app.cookies["csrftoken"]
        self.app.post(
            reverse("wombles:login"),
            params={
                "csrfmiddlewaretoken": csrftoken,
                "email": "test2@example.com",
            },
        ).follow()
