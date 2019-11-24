from django.conf import settings
from django.contrib.auth.models import User
from django.db import transaction

from candidates.models import LoggedAction
from candidates.views.version_data import get_change_metadata
from people.models import Person, PersonIdentifier
from people.helpers import clean_twitter_username


class CandidateBot(object):
    """
    A class for making edits to candidate in a way that preserves vesion
    and edit history.
    """

    SUPPORTED_EDIT_FIELDS = [
        "email",
        "other_names",
        "name",
        "twitter_username",
        "homepage_url",
        "facebook_page_url",
    ]

    def __init__(self, person_id):
        self.user = User.objects.get(username=settings.CANDIDATE_BOT_USERNAME)
        self.person = Person.objects.get(pk=person_id)
        self.edits_made = False

    def get_change_metadata_for_bot(self, source):
        """
        Wraps get_change_metadata without requiring a request object
        """
        metadata = get_change_metadata(None, source)
        metadata["username"] = self.user.username
        return metadata

    def edit_fields(self, field_dict, source, save=True):
        for field_name, field_value in field_dict.items():
            if field_name in self.SUPPORTED_EDIT_FIELDS:
                self._edit_field(field_name, field_value)

        if save:
            return self.save(source)

    def _edit_field(self, field_name, field_value):
        if field_name not in self.SUPPORTED_EDIT_FIELDS:
            raise ValueError(
                "CandidateBot can't edit {} yet".format(field_name)
            )

        value = field_value

        if field_name == "email":
            # The lightest of validation
            if "@" in value:
                if self.person.get_email:
                    raise ValueError("Email already exists")
            else:
                ValueError("{} is not a valid email".format(value))

        if field_name == "twitter_username":
            value = clean_twitter_username(value)

        PersonIdentifier.objects.update_or_create(
            person=self.person, value_type=field_name, value=value
        )
        self.edits_made = True

    def save(self, source, action_type="person-update"):
        if not self.edits_made:
            # No-op in this case
            return self.person
        with transaction.atomic():
            metadata = self.get_change_metadata_for_bot(source)
            self.person.record_version(metadata)
            self.person.save()

            LoggedAction.objects.create(
                user=self.user,
                person=self.person,
                action_type=action_type,
                ip_address=None,
                popit_person_new_version=metadata["version_id"],
                source=metadata["information_source"],
            )

        return self.person

    def add_email(self, email):
        """
        A tiny wrapper around edit_fields to make adding a single field easier
        """
        self._edit_field("email", email)

    def add_twitter_username(self, username):
        self._edit_field("twitter_username", username)

    def add_homepage_url(self, username):
        self._edit_field("homepage_url", username)

    def add_facebook_page_url(self, username):
        self._edit_field("facebook_page_url", username)
