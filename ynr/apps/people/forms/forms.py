from candidates.models import PartySet
from candidates.models.popolo_extra import Ballot
from django import forms
from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import URLValidator, validate_email
from django.utils import timezone
from django.utils.functional import cached_property
from facebook_data.tasks import extract_fb_page_id
from official_documents.models import BallotSOPN
from parties.forms import (
    PartyIdentifierField,
    PopulatePartiesMixin,
    PreviousPartyAffiliationsField,
)
from parties.models import Party
from people.forms.fields import (
    CurrentUnlockedBallotsField,
    StrippedCharField,
    UnlockedBallotsField,
)
from people.helpers import (
    clean_instagram_url,
    clean_linkedin_url,
    clean_mastodon_username,
    clean_twitter_username,
    clean_wikidata_id,
    person_names_equal,
)
from people.models import Person, PersonIdentifier
from popolo.models import Membership, OtherName


class BaseCandidacyForm(forms.Form):
    person_id = StrippedCharField(label="Person ID", max_length=256)


class CandidacyCreateForm(BaseCandidacyForm):
    source = StrippedCharField(
        label="Source of information that they're standing ({0})".format(
            settings.SOURCE_HINTS
        ),
        max_length=512,
    )


class CandidacyDeleteForm(BaseCandidacyForm):
    source = StrippedCharField(
        label="Information source for this change ({0})".format(
            settings.SOURCE_HINTS
        ),
        max_length=512,
    )


class PersonIdentifierForm(forms.ModelForm):
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

    class Meta:
        model = PersonIdentifier
        exclude = ("internal_identifier", "extra_data")

    def has_changed(self, *args, **kwargs):
        """
        The `has_changed` method tells Django if it should validate and process
        the form or not.

        In a formset it's used to detect if an "extra" form has content or not,
        so for example an empty "extra" form don't raise ValidationErrors.

        This method catches the case where someone selects a value_type from
        a drop down but doesn't add a value. As there is no new content being
        added to the site, it's safe to assume that this is an error rather
        than raising a ValidationError and forcing the user to unselect the
        value in the form.

        This method is undocumented in Django, but it seems to be the only way.
        """
        if self.instance:
            return True
        if self.changed_data == ["value_type"] and not self["value"].data:
            return False
        return super().has_changed(*args, **kwargs)

    def clean(self):
        if not self.cleaned_data.get("value", None):
            if self.cleaned_data.get("id"):
                # This is an existing PI that's been removed
                # we need to delete the model
                self.cleaned_data["id"].delete()
            self.cleaned_data["DELETE"] = True
            return self.cleaned_data
        value_type = self.cleaned_data.get("value_type")
        if not value_type:
            raise forms.ValidationError("Please select a link type.")
        if self.cleaned_data.get("value_type") in self.HTTP_IDENTIFIERS:
            # Add https schema if missing
            if not self.cleaned_data.get("value").startswith("http"):
                self.cleaned_data["value"] = (
                    f"https://{self.cleaned_data['value']}"
                )
            URLValidator()(value=self.cleaned_data["value"])
        if (
            "value_type" in self.cleaned_data
            and self.cleaned_data["value_type"]
        ):
            attr = "clean_{}".format(self.cleaned_data["value_type"])
            if hasattr(self, attr):
                try:
                    value = getattr(self, attr)(self.cleaned_data["value"])
                    self.cleaned_data["value"] = value
                except ValidationError as e:
                    self.add_error(None, e)
        return self.cleaned_data

    def clean_instagram_url(self, username):
        if self.instance.value != username:
            self.instance.internal_identifier = None
        if self.instance.internal_identifier:
            return username
        try:
            return clean_instagram_url(username)
        except ValueError as e:
            raise ValidationError(e)
        return username

    def clean_twitter_username(self, username):
        if self.instance.value != username:
            self.instance.internal_identifier = None

        if self.instance.internal_identifier:
            return username

        try:
            return clean_twitter_username(username)
        except ValueError as e:
            raise ValidationError(e)

    def clean_linkedin_url(self, url):
        if self.instance.value != url:
            self.instance.internal_identifier = None

        if self.instance.internal_identifier:
            return url

        try:
            return clean_linkedin_url(url)
        except ValueError as e:
            raise ValidationError(e)

    def clean_mastodon_username(self, username):
        if self.instance.value != username:
            self.instance.internal_identifier = None

        if self.instance.internal_identifier:
            return username

        try:
            return clean_mastodon_username(username)
        except ValueError as e:
            raise ValidationError(e)

    def clean_wikidata_id(self, identifier):
        try:
            return clean_wikidata_id(identifier)
        except ValueError as e:
            raise ValidationError(e)

    def clean_email(self, email):
        validate_email(email)
        if email.lower().endswith("parliament.uk"):
            raise ValidationError(
                "MPs are locked out of their email addresses during a general election. Please find a different email address."
            )
        return email

    def save(self, commit=True):
        ret = super().save(commit=commit)
        if commit and self.cleaned_data["value_type"].startswith("facebook"):
            extract_fb_page_id.delay(self.instance.pk)
        return ret


class PersonMembershipForm(PopulatePartiesMixin, forms.ModelForm):
    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop("user", None)
        instance: Membership = kwargs.get("instance", None)
        person: Person = kwargs.pop("person", None)
        if instance:
            initial = {
                "ballot_paper_id": kwargs["instance"].ballot.ballot_paper_id,
                "party_identifier": ["", instance.party.ec_id],
            }
            if instance.ballot.is_welsh_run:
                initial["previous_party_affiliations"] = list(
                    instance.previous_party_affiliations.values_list(
                        "ec_id", flat=True
                    )
                )
            kwargs.update(initial=initial)

        super().__init__(*args, **kwargs)
        self.fields["ballot_paper_id"] = CurrentUnlockedBallotsField(
            label="Ballot", user=self.user, person=person
        )

        if self.show_previous_party_affiliations:
            self.fields[
                "previous_party_affiliations"
            ] = PreviousPartyAffiliationsField(membership=self.instance)

    @property
    def show_previous_party_affiliations(self):
        """
        We should only include the PreviousPartyAffiliationsField if the ballot
        is welsh run, candidates and not locked, and we have a SOPN uploaded
        """
        try:
            ballot = self.instance.ballot
        except Ballot.DoesNotExist:
            return False

        if not ballot.is_welsh_run:
            return False

        if ballot.candidates_locked:
            return False

        try:
            return bool(ballot.sopn)
        except BallotSOPN.DoesNotExist:
            return False

    class Meta:
        model = Membership

        fields = ("ballot_paper_id", "party_identifier", "party_list_position")

    party_identifier = PartyIdentifierField(
        require_all_fields=False, required=True
    )
    ballot_paper_id = UnlockedBallotsField(label="Ballot")

    party_list_position = forms.IntegerField(
        max_value=20,
        min_value=1,
        required=False,
        widget=forms.NumberInput(attrs={"class": "party-list-position"}),
    )

    def save(self, commit=True):
        self.instance.ballot = self.cleaned_data["ballot_paper_id"]
        self.instance.post = self.instance.ballot.post
        party_data = self.cleaned_data["party_identifier"]
        self.instance.party = party_data["party_obj"]
        self.instance.party_name = party_data["party_name"]
        self.instance.party_description = party_data["description_obj"]
        self.instance.party_description_text = (
            party_data["description_text"] or ""
        )
        self.instance = super().save(commit)
        if "previous_party_affiliations" in self.cleaned_data:
            parties = self.cleaned_data.get("previous_party_affiliations", None)
            if parties:
                self.instance.previous_party_affiliations.set(parties)
            else:
                self.instance.previous_party_affiliations.clear()

        return self.instance

    def clean_previous_party_affiliations(self):
        parties = self.cleaned_data.get("previous_party_affiliations", None)
        if parties:
            parties = [Party.objects.get(ec_id=ec_id) for ec_id in parties]

        return parties


class BasePersonForm(forms.ModelForm):
    class Meta:
        model = Person
        exclude = (
            "membership",
            "versions",
            "not_standing",
            "edit_limitations",
            "sort_name",
            # TODO: do we actually want these on the model?
            "given_name",
            "additional_name",
            "family_name",
            "patronymic_name",
            "summary",
            "national_identity",
            "name_search_vector",
            "biography_last_updated",
            "death_date",
        )

    honorific_prefix = StrippedCharField(
        label="Title / pre-nominal honorific (e.g. Dr, Sir, etc.)",
        required=False,
    )
    name = StrippedCharField(
        label="Name (style: Ali McKay Smith not SMITH Ali McKay)",
        required=True,
        widget=forms.TextInput(attrs={"class": "person_name"}),
    )
    honorific_suffix = StrippedCharField(
        label="Post-nominal letters (e.g. CBE, DSO, etc.)", required=False
    )

    gender = StrippedCharField(
        label="Gender (e.g. “male”, “female”)", required=False
    )

    birth_date = forms.CharField(
        label="Year of birth (a four digit year)",
        required=False,
        widget=forms.NumberInput,
    )

    biography = StrippedCharField(
        label="Statement to voters",
        required=False,
        widget=forms.Textarea,
        help_text="""This must be a message from the candidate to the
                    electorate. Ideally this message will be uploaded by the
                    candidate or their agent, but crowdsourcers may find such
                    a statement on a candidate's 'About' webpage, or on
                    campaign literature.""",
    )

    favourite_biscuit = StrippedCharField(
        label="Favourite biscuit 🍪", required=False, max_length=100
    )

    source = StrippedCharField(
        label="Source of information for this change ({0})".format(
            settings.SOURCE_HINTS
        ),
        max_length=512,
        error_messages={
            "required": "You must indicate how you know about this candidate"
        },
        widget=forms.TextInput(
            attrs={
                "required": "required",
                "placeholder": "How you know about this candidate",
            }
        ),
    )

    STANDING_CHOICES = (
        ("not-sure", "Don’t Know"),
        ("standing", "Yes"),
        ("not-standing", "No"),
    )

    def clean_biography(self):
        bio = self.cleaned_data["biography"]
        if bio.find("\r"):
            bio = bio.replace("\r", "")
        # Reduce > 2 newlines to 2 newlines
        return "\n\n".join(
            [line.strip() for line in bio.split("\n\n") if line.strip()]
        )

    def save(self, commit=True, user=None):
        suggested_name = self.cleaned_data["name"]
        initial_name = self.initial["name"]
        # If the user is creating a new person,
        # or the name has changed and doesn't match the existing name
        if (
            initial_name
            and "name" in self.changed_data
            and not person_names_equal(initial_name, suggested_name)
        ):
            suggested_name = self.cleaned_data["name"]
            initial_name = self.initial["name"]
            self.instance.edit_name(
                suggested_name=suggested_name,
                initial_name=initial_name,
                user=user,
            )

        initial_biography = self.initial.get("biography", None)
        biography_updated = (
            "biography" in self.changed_data
            and initial_biography != self.cleaned_data["biography"]
        )
        if biography_updated:
            self.instance.biography_last_updated = timezone.now()

        return super().save(commit)


class NewPersonForm(PopulatePartiesMixin, BasePersonForm):
    class Meta(BasePersonForm.Meta):
        exclude = BasePersonForm.Meta.exclude + ("death_date",)

    party_identifier = PartyIdentifierField(
        require_all_fields=False, required=True
    )

    party_list_position = forms.IntegerField(
        max_value=20,
        min_value=1,
        required=False,
        widget=forms.NumberInput(attrs={"class": "party-list-position"}),
    )

    ballot_paper_id = UnlockedBallotsField(widget=forms.HiddenInput)

    def save(self, commit=True):
        person = super().save(commit)
        if person.pk:
            party_data = self.cleaned_data["party_identifier"]
            person.memberships.create(
                ballot=self.cleaned_data["ballot_paper_id"],
                party=party_data["party_obj"],
                party_name=party_data["party_name"],
                party_description=party_data["description_obj"],
                post=self.cleaned_data["ballot_paper_id"].post,
            )
        return person


class UpdatePersonForm(BasePersonForm):
    pass


class OtherNameForm(forms.ModelForm):
    class Meta:
        model = OtherName
        fields = ("name", "note", "start_date", "end_date")
        labels = {}
        help_texts = {
            "start_date": (
                "(Optional) The date from which this name would be used"
            ),
            "end_date": (
                "(Optional) The date when this name stopped being used"
            ),
        }

    source = StrippedCharField(
        label="Source",
        help_text=(
            "Please indicate how you know that this is a valid alternative name"
        ),
        max_length=512,
    )

    def clean_name(self):
        name = self.cleaned_data["name"]
        if "name" not in self.changed_data:
            return name
        name_exists = self.instance.content_object.other_names.filter(
            name=name
        ).exists()

        if name_exists:
            raise ValidationError("This other name already exists")
        return name


class AddElectionFieldsMixin(object):
    @cached_property
    def party_sets_and_party_choices(self):
        # Generating the party choices for each party set is quite
        # slow, so cache these results, so they're not fetched from
        # the database again each time add_election_fields is called.
        return [
            (
                party_set,
                Party.objects.register(party_set.slug.upper()).party_choices(
                    include_descriptions=False
                ),
            )
            for party_set in PartySet.objects.all()
        ]
