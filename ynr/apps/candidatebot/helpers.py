from django.conf import settings
from django.contrib.auth.models import User
from django.db import transaction, IntegrityError

from candidates.models import LoggedAction
from candidates.views.version_data import get_change_metadata
from people.models import Person, PersonIdentifier
from people.helpers import clean_twitter_username, clean_wikidata_id
from ynr_refactoring.settings import PersonIdentifierFields


class CandidateBot(object):
    """
    A class for making edits to candidate in a way that preserves vesion
    and edit history.
    """

    # Set this to True if you want to ignore IntegrityErrors
    # raised when adding values that already exist. Default to raise
    IGNORE_ERRORS = False

    SUPPORTED_EDIT_FIELDS = ["other_names", "name"] + [
        f.name for f in PersonIdentifierFields
    ]

    def __init__(self, person_id):
        self.user = User.objects.get(username=settings.CANDIDATE_BOT_USERNAME)
        self.person = Person.objects.get_by_id_with_redirects(person_id)
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
                self.edit_field(field_name, field_value)

        if save:
            return self.save(source)

    def edit_field(self, field_name, field_value, update=False):
        ignore_edit = False
        if field_name not in self.SUPPORTED_EDIT_FIELDS:
            raise ValueError(
                "CandidateBot can't edit {} yet".format(field_name)
            )

        field_value = field_value.strip()
        field_method = getattr(self, "clean_{}".format(field_name), None)
        if field_method:
            try:
                field_value = field_method(field_value)
            except ValueError:
                if self.IGNORE_ERRORS:
                    # We can't edit this value, but we want to ignore errors
                    # so just turn this in to a no-op
                    return None
                raise

        if hasattr(PersonIdentifierFields, field_name):
            kwargs = {"person": self.person, "value_type": field_name}
            if update:
                kwargs["defaults"] = {"value": field_value}
            else:
                kwargs["value"] = field_value
            try:
                PersonIdentifier.objects.update_or_create(**kwargs)
            except IntegrityError:
                if not update and not self.IGNORE_ERRORS:
                    raise
                if self.IGNORE_ERRORS:
                    ignore_edit = True

            if not ignore_edit:
                self.edits_made = True

    def clean_email(self, value):
        # The lightest of validation
        if "@" not in value:
            raise ValueError("{} is not a valid email".format(value))
        return value

    def clean_twitter_username(self, value):
        return clean_twitter_username(value)

    def clean_wikidata_id(self, value):
        return clean_wikidata_id(value)

    def save(self, source, action_type="person-update"):
        if not self.edits_made:
            # No-op in this case
            return self.person
        with transaction.atomic():
            metadata = self.get_change_metadata_for_bot(source)
            self.person.record_version(metadata)
            self.person.save()
            existing_action = LoggedAction.objects.filter(
                popit_person_new_version=metadata["version_id"]
            )
            if not existing_action.exists():
                LoggedAction.objects.create(
                    user=self.user,
                    person=self.person,
                    action_type=action_type,
                    ip_address=None,
                    popit_person_new_version=metadata["version_id"],
                    source=metadata["information_source"],
                )
        self.person.invalidate_identifier_cache()
        return self.person

    def add_email(self, email):
        """
        A tiny wrapper around edit_fields to make adding a single field easier
        """
        self.edit_field("email", email)

    def add_twitter_username(self, username):
        self.edit_field("twitter_username", username)

    def add_homepage_url(self, username):
        self.edit_field("homepage_url", username)

    def add_facebook_page_url(self, username):
        self.edit_field("facebook_page_url", username)
