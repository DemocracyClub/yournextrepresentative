from django.conf import settings
from django.contrib.auth.models import User

from candidates.models import LoggedAction
from candidates.views.version_data import get_change_metadata


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

    def save(self, person, msg=None):
        if msg is None:
            msg = "Updated by TwitterBot"

        metadata = self.get_change_metadata_for_bot(msg)
        person.record_version(metadata)
        person.save()

        LoggedAction.objects.create(
            user=self.user,
            person=person,
            action_type="person-update",
            ip_address=None,
            popit_person_new_version=metadata["version_id"],
            source=metadata["information_source"],
        )
