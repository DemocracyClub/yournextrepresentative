import hashlib
import json
import re

from django import forms
from people.models import Person
from splitting.provenance import COMPARABLE_FIELDS, DEFAULT_CUTOFF_DAYS
from ynr_refactoring.settings import PersonIdentifierFields

OVERRIDE_PREFIX = "override_"

# Short labels for the fields that can be split, matching the names used on
# person pages and in the edit form
FIELD_LABELS = {
    "honorific_prefix": "Title",
    "name": "Name",
    "honorific_suffix": "Post-nominal letters",
    "gender": "Gender",
    "birth_date": "Year of birth",
    "death_date": "Date of death",
    "biography": "Biography",
    "other_names": "Other names",
    "favourite_biscuit": "Favourite biscuit",
    "not_standing": "Not standing in",
    **{field.name: field.value for field in PersonIdentifierFields},
}


class MembershipChoiceField(forms.ModelChoiceField):
    def label_from_instance(self, membership):
        details = [membership.party.name]
        if membership.elected:
            details.append("elected")
        if membership.ballot.candidates_locked:
            details.append("locked")
        return f"{membership.ballot.ballot_paper_id} ({', '.join(details)})"


class PersonSplitForm(forms.Form):
    """
    The choices for splitting a candidacy off a person. The same form is
    used to preview and to confirm, so every choice can be changed until the
    split is made.
    """

    NEW = "new"

    membership = MembershipChoiceField(
        queryset=None,
        widget=forms.RadioSelect,
        empty_label=None,
        label="Candidacy to move",
    )
    destination = forms.CharField(
        initial=NEW,
        label="Destination person ID",
        help_text=(
            "Enter “new” to create a new person, or the ID of the person this "
            "candidacy belongs to. If the candidacy came from a merge, “new” "
            "brings back the person who was merged."
        ),
    )
    cutoff_days = forms.IntegerField(
        initial=DEFAULT_CUTOFF_DAYS,
        min_value=0,
        label=(
            "Restore contact details, links and biographies changed within "
            "this many days"
        ),
    )
    move_image = forms.BooleanField(
        required=False, label="Move this person's photo too"
    )
    warnings_checked = forms.BooleanField(
        required=False, label="I've checked these warnings"
    )
    preview_fingerprint = forms.CharField(
        required=False, widget=forms.HiddenInput
    )

    def __init__(self, *args, person, **kwargs):
        super().__init__(*args, **kwargs)
        self.person = person
        self.fields["membership"].queryset = person.memberships.select_related(
            "ballot", "party"
        ).order_by("-ballot__election__election_date")
        for name in COMPARABLE_FIELDS:
            label = FIELD_LABELS.get(name, name)
            self.fields[f"{OVERRIDE_PREFIX}{name}"] = forms.ChoiceField(
                choices=(
                    ("", "As suggested"),
                    ("move", "Move current value"),
                    ("keep", "Keep on this person"),
                ),
                required=False,
                label=label,
                widget=forms.Select(attrs={"aria-label": f"Change {label}"}),
            )

    def clean_destination(self):
        """
        'new', or the ID of an existing person (optionally as a URL, as
        people often paste those)
        """
        value = self.cleaned_data["destination"].strip().lower()
        if value == self.NEW:
            return value
        match = re.search(r"/person/(\d+)", value) or re.fullmatch(
            r"(\d+)", value
        )
        if not match:
            raise forms.ValidationError("Enter “new” or a person ID")
        person_id = int(match.group(1))
        if not Person.objects.filter(pk=person_id).exists():
            raise forms.ValidationError(
                f"There's no person with ID {person_id}"
            )
        return str(person_id)

    @property
    def target_person(self):
        if self.cleaned_data["destination"] == self.NEW:
            return None
        return Person.objects.get(pk=self.cleaned_data["destination"])

    @property
    def suggest(self):
        # Suggestions write details onto the other person, so they're only
        # used when that person is new or restored
        return self.cleaned_data["destination"] == self.NEW

    def override_fields(self, action):
        return [
            name
            for name in COMPARABLE_FIELDS
            if self.cleaned_data.get(f"{OVERRIDE_PREFIX}{name}") == action
        ]

    def fingerprint(self):
        """
        Identifies the choices and the person's history at preview time, so
        a split only happens if nothing has changed since it was previewed
        """
        versions = self.person.versions or []
        data = {
            "person_version": versions[0]["version_id"] if versions else "",
            "membership": self.cleaned_data["membership"].pk,
            "destination": self.cleaned_data["destination"],
            "cutoff_days": self.cleaned_data["cutoff_days"],
            "move_image": self.cleaned_data["move_image"],
            "move": self.override_fields("move"),
            "keep": self.override_fields("keep"),
        }
        return hashlib.sha256(
            json.dumps(data, sort_keys=True).encode()
        ).hexdigest()
