import json

from django import forms
from django.core.exceptions import ValidationError
from django.core.validators import URLValidator, validate_email
from django.template.loader import render_to_string
from django.utils.safestring import SafeText, mark_safe
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
    template_name = "bulk_add/widgets/person_identifier_multiwidget.html"

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


class PersonIdentifierWidgetSet(forms.MultiWidget):
    def __init__(self, *args, **kwargs):
        super().__init__(
            widgets=[
                PersonIdentifierWidget(),
                PersonIdentifierWidget(),
                PersonIdentifierWidget(),
            ],
            **kwargs,
        )

    def decompress(self, value):
        if value:
            return [{k: v} for k, v in value.items()]
        return [None, None, None]


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
        if not data_list:
            return None
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


class PersonIdentifierFieldSet(forms.MultiValueField):
    def __init__(self, **kwargs):
        fields = (
            PersonIdentifierField(
                required=False,
            ),
            PersonIdentifierField(
                required=False,
            ),
            PersonIdentifierField(
                required=False,
            ),
        )
        widget = PersonIdentifierWidgetSet()

        super().__init__(
            fields=fields,
            require_all_fields=False,
            widget=widget,
            **kwargs,
        )

    def compress(self, data_list):
        person_identifiers = {}
        for pi in data_list:
            if pi:
                person_identifiers.update(pi)
        return json.dumps(person_identifiers)


class PersonSuggestionRadioSelect(forms.RadioSelect):
    def create_option(
        self, name, value, label, selected, index, subindex=None, attrs=None
    ):
        option = super().create_option(
            name, value, label, selected, index, subindex=subindex, attrs=attrs
        )
        if value == "_new":
            return option
        option["instance"] = value.instance
        option["other_names"] = value.instance.other_names.all()
        option["previous_candidacies"] = self.get_previous_candidacies(
            value.instance
        )
        return option

    def get_previous_candidacies(self, person):
        previous = []
        candidacies = (
            person.memberships.select_related(
                "ballot__post", "ballot__election", "party"
            )
            .select_related("ballot__sopn")
            .order_by("-ballot__election__election_date")[:3]
        )

        for candidacy in candidacies:
            party = candidacy.party
            party_str = f"{party.name}"
            if person.new_party == party.ec_id:
                party_str = f"<strong>{party.name}</strong>"

            election = candidacy.ballot.election
            election_str = f"{election.name}"
            if person.new_organisation == election.organization.pk:
                election_str = f"<strong>{election.name}</strong>"

            text = """{election}: {post} – {party}""".format(
                post=candidacy.ballot.post.short_label,
                election=election_str,
                party=party_str,
            )
            sopn = candidacy.ballot.officialdocument_set.first()
            if sopn:
                text += ' (<a href="{0}">SOPN</a>)'.format(
                    sopn.get_absolute_url()
                )
            previous.append(SafeText(text))
        return previous


class PersonSuggestionModelChoiceField(forms.ModelChoiceField):
    """
    For use on the review page to show each suggested person as a radio field.
    """

    def label_from_instance(self, obj):
        # Render using a template fragment per object
        html = render_to_string(
            "bulk_add/widgets/person_suggestion_choice_label.html",
            {"object": obj},
        )
        return mark_safe(html)

    def to_python(self, value):
        if value == "_new":
            return value
        for model in self.queryset:
            if str(model.pk) == value:
                return model.pk
        return super().to_python(value)
