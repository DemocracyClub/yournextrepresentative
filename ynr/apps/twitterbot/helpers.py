import requests
from candidates.models import LoggedAction
from candidates.models.db import EditType
from candidates.views.version_data import get_change_metadata
from django.conf import settings
from django.contrib.auth.models import User


class TwitterBot(object):
    """
    A class for making edits in a way that preserves version and edit history.

    """

    def __init__(self):
        self.user = User.objects.get(username=settings.TWITTER_BOT_USERNAME)

    def get_change_metadata_for_bot(self, source):
        """
        Wraps get_change_metadata without requiring a request object

        """
        metadata = get_change_metadata(None, source)
        metadata["username"] = self.user.username
        return metadata

    def is_user_suspended(self, screen_name):
        """
        Makes a request for a single user, and checks for any errors with code
        63 as this means the account was suspended
        https://developer.twitter.com/en/support/twitter-api/error-troubleshooting#error-codes
        """
        token = settings.TWITTER_APP_ONLY_BEARER_TOKEN
        headers = {"Authorization": f"Bearer {token}"}
        response = requests.get(
            "https://api.twitter.com/1.1/users/show.json",
            params={"screen_name": screen_name},
            headers=headers,
        )
        errors = response.json().get("errors", [])
        return any(error["code"] == 63 for error in errors)

    def handle_suspended(self, identifier):
        """
        Checks if we already knew about the suspension, and if not logs it
        """
        person = identifier.person
        status = identifier.extra_data.get("status")
        if status == "suspended":
            # already knew suspended so nothing new to log
            return

        # this is either the first time we have seen that the user is suspended
        # or a new suspension so change the status, count and log it
        suspension_count = identifier.extra_data.get("suspension_count", 0)
        suspension_count += 1
        identifier.extra_data["suspension_count"] = suspension_count
        identifier.extra_data["status"] = "suspended"
        identifier.save()
        self.save(
            person=person,
            msg="User's twitter account is suspended",
            action_type="suspended-twitter-account",
        )

    def save(self, person, msg=None, action_type=None):
        msg = msg or "Updated by TwitterBot"
        action_type = action_type or "person-update"

        metadata = self.get_change_metadata_for_bot(msg)
        person.record_version(metadata)
        person.save()

        LoggedAction.objects.create(
            user=self.user,
            person=person,
            action_type=action_type,
            ip_address=None,
            popit_person_new_version=metadata["version_id"],
            source=metadata["information_source"],
            edit_type=EditType.BOT.name,
        )
