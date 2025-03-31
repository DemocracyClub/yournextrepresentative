from django import forms
from django.core.exceptions import ValidationError
from django.core.validators import URLValidator, validate_email
from people.helpers import (
    clean_instagram_url,
    clean_linkedin_url,
    clean_mastodon_username,
    clean_twitter_username,
    clean_wikidata_id,
)
from people.models import PersonIdentifier

HTTP_IDENTIFIERS = [
    "homepage_url",
    "facebook_personal_url",
    "party_ppc_page_url",
    "linkedin_url",
    "facebook_page_url",
    "wikipedia_url",
    "blue_sky_url",
    "threads_url",
    "other_url",
    "tiktok_url",
]


def clean_email(email):
    validate_email(email)
    if email.lower().endswith("parliament.uk"):
        raise ValueError(
            "MPs are locked out of their email addresses during a general election. Please find a different email address."
        )
    return email


class PersonIdentifierWidget(forms.MultiWidget):
    template_name = "bulk_add/includes/person_identifier_multiwidget.html"

    def __init__(self, *args, **kwargs):
        super().__init__(
            widgets=[
                forms.TextInput(),
                forms.Select(
                    choices=[("", "Select an option")]
                    + PersonIdentifier.objects.select_choices()[1:],
                ),
            ],
            **kwargs,
        )

    def decompress(self, value):
        if value:
            pid_type, pid = next(iter(value.items()))
            return [pid, pid_type]
        return [None, None]


class PersonIdentifierField(forms.MultiValueField):
    def __init__(self, **kwargs):
        fields = (
            forms.CharField(
                required=True,
                error_messages={
                    "incomplete": "Please enter a social media link",
                },
            ),
            forms.ChoiceField(
                required=True,
                error_messages={
                    "incomplete": "Please select a link type",
                },
                choices=[("", "Select an option")]
                + PersonIdentifier.objects.select_choices()[1:],
            ),
        )
        widget = PersonIdentifierWidget()

        super().__init__(
            fields=fields,
            require_all_fields=False,
            widget=widget,
            **kwargs,
        )

    def compress(self, data_list):
        pid = data_list[0]
        pid_type = data_list[1]
        # Validate URLs:
        if pid_type in HTTP_IDENTIFIERS:
            # Add https schema if missing
            if not pid.startswith("http"):
                pid = f"https://{pid}"
            URLValidator()(pid)

        # Validate pid:
        try:
            if pid_type == "instagram_url":
                clean_instagram_url(pid)
            elif pid_type == "linkedin_url":
                clean_linkedin_url(pid)
            elif pid_type == "mastodon_url":
                clean_mastodon_username(pid)
            elif pid_type == "twitter_url":
                clean_twitter_username(pid)
            elif pid_type == "wikidata_id":
                clean_wikidata_id(pid)
            elif pid_type == "email":
                clean_email(pid)
        except ValueError as e:
            raise ValidationError(e)

        return {pid_type: pid}
