import hashlib
import hmac
import json
import time
from unittest.mock import patch
from urllib.parse import urlencode

from candidates.models.db import LoggedAction
from candidates.tests.auth import TestUserMixin
from django.test import TestCase, override_settings
from django.urls import reverse

SIGNING_SECRET = "test-slack-signing-secret"


def make_body(pk, username="john"):
    payload = {
        "user": {"username": username},
        "response_url": "https://slack.example.com/response",
        "message": {
            "blocks": [
                {"type": "section", "text": {"text": "one"}},
                {"type": "section", "text": {"text": "two"}},
            ]
        },
        "actions": [
            {
                "action_id": "candidate-edit-review-approve",
                "value": str(pk),
            }
        ],
    }
    return urlencode({"payload": json.dumps(payload)}).encode("utf-8")


def make_signature_headers(body, secret=SIGNING_SECRET, timestamp=None):
    if timestamp is None:
        timestamp = str(int(time.time()))
    basestring = f"v0:{timestamp}:".encode() + body
    signature = (
        "v0="
        + hmac.new(secret.encode(), basestring, hashlib.sha256).hexdigest()
    )
    return {
        "HTTP_X_SLACK_REQUEST_TIMESTAMP": timestamp,
        "HTTP_X_SLACK_SIGNATURE": signature,
    }


@override_settings(SLACK_SIGNING_SECRET=SIGNING_SECRET)
class TestSlackHookRouter(TestUserMixin, TestCase):
    def setUp(self):
        self.action = LoggedAction.objects.create(
            user=self.user,
            action_type="person-update",
            popit_person_new_version="8aa71db8f2f20bf8",
            source="test",
        )
        self.url = reverse("slack-hooks")

    def post_body(self, body, **header_overrides):
        headers = make_signature_headers(body)
        headers.update(header_overrides)
        return self.client.post(
            self.url,
            data=body,
            content_type="application/x-www-form-urlencoded",
            **headers,
        )

    def test_missing_signature_headers_rejected(self):
        body = make_body(self.action.pk)
        response = self.client.post(
            self.url,
            data=body,
            content_type="application/x-www-form-urlencoded",
        )
        self.assertEqual(response.status_code, 403)
        self.action.refresh_from_db()
        self.assertIsNone(self.action.approved)

    def test_invalid_signature_rejected(self):
        body = make_body(self.action.pk)
        response = self.post_body(body, HTTP_X_SLACK_SIGNATURE="v0=" + "0" * 64)
        self.assertEqual(response.status_code, 403)
        self.action.refresh_from_db()
        self.assertIsNone(self.action.approved)

    def test_expired_timestamp_rejected(self):
        body = make_body(self.action.pk)
        old_timestamp = str(int(time.time()) - 60 * 10)
        headers = make_signature_headers(body, timestamp=old_timestamp)
        response = self.client.post(
            self.url,
            data=body,
            content_type="application/x-www-form-urlencoded",
            **headers,
        )
        self.assertEqual(response.status_code, 403)
        self.action.refresh_from_db()
        self.assertIsNone(self.action.approved)

    def test_missing_signing_secret_rejects_even_valid_signature(self):
        body = make_body(self.action.pk)
        with override_settings(SLACK_SIGNING_SECRET=None):
            response = self.post_body(body)
        self.assertEqual(response.status_code, 403)

    def test_tampered_body_rejected(self):
        # Signature is computed over the original body, but a different
        # body is sent - simulating an attacker modifying the payload
        # after a signature was captured.
        body = make_body(self.action.pk)
        headers = make_signature_headers(body)
        tampered_body = make_body(self.action.pk, username="mallory")
        response = self.client.post(
            self.url,
            data=tampered_body,
            content_type="application/x-www-form-urlencoded",
            **headers,
        )
        self.assertEqual(response.status_code, 403)
        self.action.refresh_from_db()
        self.assertIsNone(self.action.approved)

    def test_valid_signature_marks_action_approved(self):
        body = make_body(self.action.pk)
        with patch("moderation_queue.slack.requests.post") as mock_post:
            response = self.post_body(body)
        mock_post.assert_called_once()
        self.assertEqual(response.status_code, 200)
        self.action.refresh_from_db()
        self.assertIsNotNone(self.action.approved)
        self.assertEqual(self.action.approved["username"], "john")
