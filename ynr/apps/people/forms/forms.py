from django import forms
from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import validate_email
from django.utils.functional import cached_property
from candidates.models import PartySet
from facebook_data.tasks import extract_fb_page_id
from parties.models import Party
from people.forms.fields import (
    CurrentUnlockedBallotsField,
    StrippedCharField,
    BlankApproximateDateFormField,
)
from parties.forms import PartyIdentifierField, PopulatePartiesMixin
from people.models import Person, PersonIdentifier
from popolo.models import OtherName, Membership

from people.helpers import clean_twitter_username, clean_wikidata_id

# TODO: Use with JS
# def get_ballot_choices(election, user=None):
#     """
#     Returns a list formatted for passing to a SelectWithAttrs widget
#     :type user: django.contrib.auth.models.User
#     :type election: elections.models.Election
#     :param user:
#     :return:
#     """
#     user_can_edit_cancelled = False
#     if user and user.is_staff:
#         user_can_edit_cancelled = True
#     ballots_qs = (
#         Ballot.objects.filter(election=election)
#         .select_related("post", "election")
#         .order_by("post__label")
#     )
#
#     choices = [("", "")]
#     for ballot in ballots_qs:
#         attrs = {}
#         ballot_label = ballot.post.short_label
#         if ballot.cancelled:
#             ballot_label = "{} {}".format(
#                 ballot_label, ballot.cancelled_status_text
#             )
#             if not user_can_edit_cancelled:
#                 attrs["disabled"] = True
#
#         if ballot.candidates_locked:
#             ballot_label = "{} {}".format(
#                 ballot_label, ballot.locked_status_text
#             )
#             attrs["disabled"] = True
#
#         attrs["label"] = ballot_label
#
#         choices.append((ballot.post.slug, attrs))
#     return choices


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
        else:
            return super().has_changed(*args, **kwargs)

    def clean(self):
        if not self.cleaned_data.get("value", None):
            if self.cleaned_data.get("id"):
                # This is an existing PI that's been removed
                # we need to delete the model
                self.cleaned_data["id"].delete()
            self.cleaned_data["DELETE"] = True
            return self.cleaned_data

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

    def clean_twitter_username(self, username):
        if self.instance.value != username:
            self.instance.internal_identifier = None
        try:
            return clean_twitter_username(username)
        except ValueError as e:
            raise ValidationError(e)

    def clean_wikidata_id(self, identifier):
        try:
            return clean_wikidata_id(identifier)
        except ValueError as e:
            raise ValidationError(e)

    def clean_email(self, email):
        validate_email(email)
        return email

    def save(self, commit=True):
        ret = super().save(commit=commit)
        if commit and self.cleaned_data["value_type"].startswith("facebook"):
            extract_fb_page_id.delay(self.instance.pk)
        return ret


class PersonMembershipForm(PopulatePartiesMixin, forms.ModelForm):
    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop("user", None)
        if kwargs.get("instance", None):
            kwargs.update(
                initial={
                    "ballot_paper_id": kwargs[
                        "instance"
                    ].ballot.ballot_paper_id,
                    "party_identifier": ["", kwargs["instance"].party.ec_id],
                }
            )

        super().__init__(*args, **kwargs)
        self.fields["ballot_paper_id"] = CurrentUnlockedBallotsField(
            label="Ballot", user=self.user
        )

    class Meta:
        model = Membership

        fields = ("ballot_paper_id", "party_identifier", "party_list_position")

    party_identifier = PartyIdentifierField(
        require_all_fields=False, required=True
    )
    ballot_paper_id = CurrentUnlockedBallotsField(label="Ballot")

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
        self.instance.party_description = party_data["description_text"]
        return super().save(commit)


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
        )

    honorific_prefix = StrippedCharField(
        label="Title / pre-nominal honorific (e.g. Dr, Sir, etc.)",
        required=False,
    )
    name = StrippedCharField(
        label="Name (style: Ali Smith not SMITH Ali)", required=True
    )
    honorific_suffix = StrippedCharField(
        label="Post-nominal letters (e.g. CBE, DSO, etc.)", required=False
    )

    gender = StrippedCharField(
        label="Gender (e.g. “male”, “female”)", required=False
    )

    birth_date = BlankApproximateDateFormField(
        label="Date of birth (a four digit year or a full date)", required=False
    )
    death_date = BlankApproximateDateFormField(
        label="Date of death (a four digit year or a full date)", required=False
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
        label="Favourite biscuit 🍪", required=False
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


class NewPersonForm(BasePersonForm):
    # TODO: Deal with party lists
    class Meta(BasePersonForm.Meta):
        exclude = BasePersonForm.Meta.exclude + ("death_date",)

    party_identifier = PartyIdentifierField(
        require_all_fields=False, required=True
    )
    ballot_paper_id = CurrentUnlockedBallotsField(widget=forms.HiddenInput)

    def save(self, commit=True):
        person = super().save(commit)
        if person.pk:
            party_data = self.cleaned_data["party_identifier"]
            person.memberships.create(
                ballot=self.cleaned_data["ballot_paper_id"],
                party=party_data["party_obj"],
                party_name=party_data["party_name"],
                party_description=party_data["description_text"],
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
