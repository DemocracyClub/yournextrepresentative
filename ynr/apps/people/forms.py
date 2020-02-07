from django import forms
from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import validate_email
from django.db.models import Count
from django.utils.functional import cached_property

from candidates.models import (
    PartySet,
    UnsafeToDelete,
    raise_if_unsafe_to_delete,
)
from elections.models import Election
from facebook_data.tasks import extract_fb_page_id
from parties.models import Party
from people.helpers import parse_approximate_date
from people.models import Person, PersonIdentifier
from popolo.models import OtherName, Post

from .helpers import clean_twitter_username, clean_wikidata_id


class StrippedCharField(forms.CharField):
    """A backport of the Django 1.9 ``CharField`` ``strip`` option.

    If ``strip`` is ``True`` (the default), leading and trailing
    whitespace is removed.
    """

    def __init__(
        self, max_length=None, min_length=None, strip=True, *args, **kwargs
    ):
        self.strip = strip
        super().__init__(
            max_length=max_length, min_length=min_length, *args, **kwargs
        )

    def to_python(self, value):
        value = super().to_python(value)
        if self.strip:
            value = value.strip()
        return value


class BaseCandidacyForm(forms.Form):
    person_id = StrippedCharField(label="Person ID", max_length=256)
    post_id = StrippedCharField(label="Post ID", max_length=256)


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


PersonIdentifierFormsetFactory = forms.inlineformset_factory(
    Person,
    PersonIdentifier,
    form=PersonIdentifierForm,
    can_delete=True,
    widgets={
        "value_type": forms.Select(
            choices=PersonIdentifier.objects.select_choices()
        )
    },
)


class BasePersonForm(forms.Form):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        for field in settings.SIMPLE_POPOLO_FIELDS:
            opts = {"label": field.label, "required": field.required}

            if field.name == "biography":
                opts[
                    "help_text"
                ] = """
                    This must be a message from the candidate to the
                    electorate. Ideally this message will be uploaded by the
                    candidate or their agent, but crowdsourcers may find such
                    a statement on a candidate's 'About' webpage, or on
                    campaign literature."""
                opts["label"] = "Statement to voters"

            if field.name == "name":
                opts["label"] = "Name (style: Ali Smith not SMITH Ali)"

            if field.info_type_key == "url":
                self.fields[field.name] = forms.URLField(**opts)
            # elif field.info_type_key == "email":
            #     self.fields[field.name] = forms.EmailField(**opts)
            elif field.info_type_key == "text_multiline":
                opts["widget"] = forms.Textarea
                self.fields[field.name] = StrippedCharField(**opts)
            else:
                self.fields[field.name] = StrippedCharField(**opts)

        self.fields["favourite_biscuit"] = StrippedCharField(
            label="Favourite biscuit 🍪", required=False
        )

    STANDING_CHOICES = (
        ("not-sure", "Don’t Know"),
        ("standing", "Yes"),
        ("not-standing", "No"),
    )

    def _clean_date(self, date):
        if not date:
            return ""

        if len(date) > 20:
            raise ValidationError("The date entered was too long")
        try:
            parsed_date = parse_approximate_date(date)
        except ValueError:
            raise ValidationError(
                "That date of birth could not be understood. Try using DD/MM/YYYY instead"
            )
        return parsed_date

    def clean_birth_date(self):
        birth_date = self.cleaned_data["birth_date"]
        return self._clean_date(birth_date)

    def clean_death_date(self):
        death_date = self.cleaned_data["death_date"]
        return self._clean_date(death_date)

    def check_party_and_constituency_are_selected(self, cleaned_data):
        """This is called by the clean method of subclasses"""

        for election_data in self.elections_with_fields:
            election = election_data.slug
            election_name = election_data.name

            standing_status = cleaned_data.get(
                "standing_" + election, "standing"
            )
            if standing_status != "standing":
                continue

            # Make sure that there is a party selected; we need to do this
            # from the clean method rather than single field validation
            # since the party field that should be checked depends on the
            # selected constituency.
            post_key = "constituency_" + election
            post_id = cleaned_data.get(post_key, None)

            if not post_id:
                # If there's already an error about this field, don't add
                # another one
                if post_key in self.errors:
                    return cleaned_data
                else:
                    message = (
                        "If you mark the candidate as standing in the "
                        "{election}, you must select a post"
                    )
                    raise forms.ValidationError(
                        message.format(election=election_name)
                    )
            # Check that that post actually exists:
            post_qs = Post.objects.filter(
                slug=post_id, ballot__election=election_data
            )
            if not post_qs.exists():
                message = "An unknown post ID '{post_id}' was specified"
                raise forms.ValidationError(message.format(post_id=post_id))
            try:
                party_set = PartySet.objects.get(post=post_qs.get())
            except PartySet.DoesNotExist:
                message = (
                    "Could not find parties for the post with ID "
                    "'{post_id}' in the {election}"
                )
                raise forms.ValidationError(
                    message.format(post_id=post_id, election=election_name)
                )
            party_field = "party_" + party_set.slug.upper() + "_" + election
            try:
                party_id = cleaned_data[party_field]
            except ValueError:
                party_id = None
            if not Party.objects.filter(ec_id=party_id).exists():
                message = "You must specify a party for the {election}"
                raise forms.ValidationError(
                    message.format(election=election_name)
                )
        return cleaned_data


class NewPersonForm(BasePersonForm):
    def __init__(self, *args, **kwargs):

        election = kwargs.pop("election", None)
        hidden_post_widget = kwargs.pop("hidden_post_widget", None)
        super().__init__(*args, **kwargs)

        election_data = Election.objects.get_by_slug(election)

        standing_field_kwargs = {
            "label": "Standing in %s" % election_data.name,
            "choices": self.STANDING_CHOICES,
        }
        if hidden_post_widget:
            standing_field_kwargs["widget"] = forms.HiddenInput()
        else:
            standing_field_kwargs["widget"] = forms.Select(
                attrs={"class": "standing-select"}
            )
        self.fields["standing_" + election] = forms.ChoiceField(
            **standing_field_kwargs
        )

        self.elections_with_fields = [election_data]

        post_field_kwargs = {
            "label": "Post in the {election}".format(
                election=election_data.name
            ),
            "max_length": 256,
        }
        if hidden_post_widget:
            post_field_kwargs["widget"] = forms.HiddenInput()
            post_field = StrippedCharField(**post_field_kwargs)
        else:
            post_field = forms.ChoiceField(
                label="Post in the {election}".format(
                    election=election_data.name
                ),
                required=False,
                choices=[("", "")]
                + sorted(
                    [
                        (post.slug, post.short_label)
                        for post in Post.objects.filter(
                            elections__slug=election
                        )
                    ],
                    key=lambda t: t[1],
                ),
                widget=forms.Select(attrs={"class": "post-select"}),
            )

        self.fields["constituency_" + election] = post_field

        # It seems to be common in elections around the world for
        # there to be different sets of parties that candidates can
        # stand for depending on, for example, where in the country
        # they're standing. (For example, in the UK General Election,
        # there is a different register of parties for Northern
        # Ireland and Great Britain constituencies.) We create a party
        # choice field for each such "party set" and make sure only
        # the appropriate one is shown, depending on the election and
        # selected constituency, using Javascript.
        specific_party_set = None
        if hidden_post_widget:
            # Then the post can't be changed, so only add the
            # particular party set relevant for that post:
            post_id = kwargs["initial"]["constituency_" + election]
            post_obj = Post.objects.get(
                slug=post_id, ballot__election=election_data
            )
            specific_party_set = PartySet.objects.get(post=post_obj)

        party_registers_for_election = set(
            election_data.ballot_set.annotate(
                Count("post__party_set__slug")
            ).values_list("post__party_set__slug", flat=True)
        )
        for register in party_registers_for_election:
            register = register.upper()
            if specific_party_set and (
                register != specific_party_set.slug.upper()
            ):
                continue

            self.fields[
                "party_" + register + "_" + election
            ] = forms.ChoiceField(
                label="Party in {election} ({register})".format(
                    election=election_data.name, register=register
                ),
                choices=Party.objects.register(register).party_choices(),
                required=False,
                widget=forms.Select(
                    attrs={"class": "party-select party-select-" + election}
                ),
            )

            if election_data.party_lists_in_use:
                # Then add a field to enter the position on the party list
                # as an integer:
                field_name = "party_list_position_" + register + "_" + election
                self.fields[field_name] = forms.IntegerField(
                    label=(
                        "Position in party list ('1' for first, '2' for second, etc.)"
                    ),
                    min_value=1,
                    required=False,
                    widget=forms.NumberInput(
                        attrs={
                            "class": "party-position party-position-" + election
                        }
                    ),
                )

    source = StrippedCharField(
        label="Source of information ({0})".format(settings.SOURCE_HINTS),
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

    def clean(self):
        cleaned_data = super().clean()
        return self.check_party_and_constituency_are_selected(cleaned_data)


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

    def add_elections_fields(self, elections):
        for election_data in elections:
            self.add_election_fields(election_data)

    def add_election_fields(self, election_data):
        election = election_data.slug
        self.fields["standing_" + election] = forms.ChoiceField(
            label="Standing in %s" % election_data.name,
            choices=BasePersonForm.STANDING_CHOICES,
            widget=forms.Select(attrs={"class": "standing-select"}),
        )
        self.fields["constituency_" + election] = forms.ChoiceField(
            label="Constituency in %s" % election_data.name,
            required=False,
            choices=[("", "")]
            + sorted(
                [
                    (post.slug, post.short_label)
                    for post in Post.objects.filter(elections__slug=election)
                ],
                key=lambda t: t[1],
            ),
            widget=forms.Select(attrs={"class": "post-select"}),
        )
        for party_set, party_choices in self.party_sets_and_party_choices:
            self.fields[
                "party_" + party_set.slug.upper() + "_" + election
            ] = forms.ChoiceField(
                label="Party in {election} ({party_set_name})".format(
                    election=election_data.name, party_set_name=party_set.name
                ),
                choices=party_choices,
                required=False,
                widget=forms.Select(
                    attrs={"class": "party-select party-select-" + election}
                ),
            )
            if election_data.party_lists_in_use:
                # Then add a field to enter the position on the party list
                # as an integer:
                field_name = (
                    "party_list_position_"
                    + party_set.slug.upper()
                    + "_"
                    + election
                )
                self.fields[field_name] = forms.IntegerField(
                    label=(
                        "Position in party list ('1' for first, '2' for second, etc.)"
                    ),
                    min_value=1,
                    required=False,
                    widget=forms.NumberInput(
                        attrs={
                            "class": "party-position party-position-" + election
                        }
                    ),
                )


class UpdatePersonForm(AddElectionFieldsMixin, BasePersonForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.elections_with_fields = list(
            Election.objects.filter(
                ballot__membership__person=self.initial["person"]
            )
            .future()
            .order_by("-election_date")
        )
        # The fields on this form depends on how many elections are
        # going on at the same time. (FIXME: this might be better done
        # with formsets?)
        self.add_elections_fields(self.elections_with_fields)

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

    def clean(self):
        if "extra_election_id" in self.data:
            # We're adding a new election
            election = Election.objects.get(slug=self.data["extra_election_id"])

            # Add this new election to elections_with_fields
            if election not in self.elections_with_fields:
                self.elections_with_fields.append(election)

            # Then re-create the form with the new election in
            self.add_elections_fields(self.elections_with_fields)

            # Now we need to re-clean the data, with the new election in it
            self._clean_fields()

        for field in self.changed_data:
            if field.startswith("constituency_"):
                # We're changing a constituency, so we need to make sure
                # that's allowed
                if self.initial.get(field):
                    membership = self.initial["person"].memberships.get(
                        ballot__post__slug=self.initial[field],
                        ballot__election__slug=field.replace(
                            "constituency_", ""
                        ),
                    )
                    try:
                        raise_if_unsafe_to_delete(membership)
                    except UnsafeToDelete as e:
                        self.add_error(field, e)

        cleaned_data = super().clean()
        return self.check_party_and_constituency_are_selected(cleaned_data)


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
        name_exists = self.instance.content_object.other_names.filter(
            name=name
        ).exists()

        if name_exists:
            raise ValidationError("This other name already exists")
        return name
