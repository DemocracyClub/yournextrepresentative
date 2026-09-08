import hashlib
import hmac
import random
import time

from django.conf import settings
from slacker2 import Slacker

# Reject requests whose timestamp is further than this many seconds from
# "now", to protect against replay attacks. This matches Slack's own
# recommendation of five minutes.
SLACK_REQUEST_MAX_AGE_SECONDS = 60 * 5


class SlackSignatureVerificationError(Exception):
    """
    Raised when an inbound request can't be verified as having genuinely
    come from Slack.
    """


def verify_slack_request(request):
    """
    Verify that a request to a Slack webhook endpoint genuinely came from
    Slack, by checking the `X-Slack-Signature` HMAC-SHA256 signature of the
    raw request body, as described at:
    https://api.slack.com/authentication/verifying-requests-from-slack

    Raises SlackSignatureVerificationError if the request can't be
    verified. Callers MUST NOT process the request body unless this
    function returns without raising.
    """
    signing_secret = settings.SLACK_SIGNING_SECRET
    if not signing_secret:
        raise SlackSignatureVerificationError(
            "SLACK_SIGNING_SECRET is not configured"
        )

    timestamp = request.headers.get("X-Slack-Request-Timestamp")
    signature = request.headers.get("X-Slack-Signature")
    if not timestamp or not signature:
        raise SlackSignatureVerificationError("Missing Slack signature headers")

    try:
        timestamp_int = int(timestamp)
    except ValueError as e:
        raise SlackSignatureVerificationError("Invalid timestamp header") from e

    if abs(time.time() - timestamp_int) > SLACK_REQUEST_MAX_AGE_SECONDS:
        raise SlackSignatureVerificationError(
            "Request timestamp is outside of the allowed window"
        )

    basestring = b"v0:" + timestamp.encode("utf-8") + b":" + request.body
    expected_signature = (
        "v0="
        + hmac.new(
            signing_secret.encode("utf-8"), basestring, hashlib.sha256
        ).hexdigest()
    )

    if not hmac.compare_digest(expected_signature, signature):
        raise SlackSignatureVerificationError("Signature mismatch")


class SlackHelper:
    def __init__(self, user=settings.CANDIDATE_BOT_USERNAME):
        self.FAKE_MODE = not hasattr(settings, "SLACK_TOKEN")
        if not self.FAKE_MODE:
            self.client = Slacker(settings.SLACK_TOKEN)
        self.user = user

    def post_message(
        self, to, message_text, blocks=None, attachments=None, extra_dict=None
    ):
        kwargs = {
            "username": self.user,
            "icon_emoji": ":robot_face:",
            "text": message_text,
            "attachments": attachments,
            "blocks": blocks,
        }
        if extra_dict:
            kwargs.update(extra_dict)
        if not self.FAKE_MODE:
            self.client.chat.post_message(to, **kwargs)

    @property
    def random_happy(self):
        return random.choice(
            [
                ":+1:",
                ":tada:",
                ":grinning:",
                ":heart_eyes:",
                ":heart_eyes_cat:",
                ":heart:",
                ":laughing:",
                ":sunny:",
                ":white_check_mark:",
                ":star:",
                ":smile:",
            ]
        )

    @property
    def random_sad(self):
        return random.choice(
            [
                ":-1:",
                ":disappointed:",
                ":confused:",
                ":unamused:",
                ":rage:",
                ":confounded:",
                ":hankey:",
                ":red_circle:",
                ":x:",
                ":cry:",
            ]
        )
