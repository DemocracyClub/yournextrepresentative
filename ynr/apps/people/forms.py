from elections.models import Election

from django import forms
from django.core.validators import validate_email
from django.conf import settings
from django.core.exceptions import ValidationError
from django.db.models import Count
from django.utils.functional import cached_property
from django.utils.translation import ugettext_lazy as _

from candidates.models import PartySet
from popolo.models import OtherName, Post
from people.helpers import parse_approximate_date
from people.models import Person, PersonIdentifier
from parties.models import Party

from .helpers import clean_twitter_username


class StrippedCharField(forms.CharField):
    """A backport of the Django 1.9 ``CharField`` ``strip`` option.

    If ``strip`` is ``True`` (the default), leading and trailing
    whitespace is removed.
    """

    def __init__(
        self, max_length=None, min_length=None, strip=True, *args, **kwargs
    ):
        self.strip = strip
        super().__init__(max_length, min_length, *args, **kwargs)

    def to_python(self, value):
        value = super().to_python(value)
        if self.strip:
            value = value.strip()
        return value


class BaseCandidacyForm(forms.Form):
    person_id = StrippedCharField(label=_("Person ID"), max_length=256)
    post_id = StrippedCharField(label=_("Post ID"), max_length=256)


class CandidacyCreateForm(BaseCandidacyForm):
    source = StrippedCharField(
        label=_("Source of information that they're standing ({0})").format(
            settings.SOURCE_HINTS
        ),
        max_length=512,
    )


class CandidacyDeleteForm(BaseCandidacyForm):
    source = StrippedCharField(
        label=_("Information source for this change ({0})").format(
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
        try:
            return clean_twitter_username(username)
        except ValueError as e:
            raise ValidationError(e)

    def clean_email(self, email):
        validate_email(email)
        return email


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
            opts = {"label": _(field.label), "required": field.required}

            if field.name == "biography":
                opts["help_text"] = _(
                    """
                    This must be a message from the candidate to the
                    electorate. Ideally this message will be uploaded by the
                    candidate or their agent, but crowdsourcers may find such
                    a statement on a candidate's 'About' webpage, or on
                    campaign literature."""
                )
                opts["label"] = _("Statement to voters")

            if field.name == "name":
                opts["label"] = _("Name (style: Ali Smith not SMITH Ali)")

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
        ("not-sure", _("Don’t Know")),
        ("standing", _("Yes")),
        ("not-standing", _("No")),
    )

    def clean_birth_date(self):
        birth_date = self.cleaned_data["birth_date"]
        if not birth_date:
            return ""
        try:
            parsed_date = parse_approximate_date(birth_date)
        except ValueError:
            if settings.DD_MM_DATE_FORMAT_PREFERRED:
                message = _(
                    "That date of birth could not be understood. Try using DD/MM/YYYY instead"
                )
            else:
                message = _(
                    "That date of birth could not be understood. Try using MM/DD/YYYY instead"
                )
            raise ValidationError(message)
        return parsed_date

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
            post_id = cleaned_data["constituency_" + election]
            if not post_id:
                message = _(
                    "If you mark the candidate as standing in the "
                    "{election}, you must select a post"
                )
                raise forms.ValidationError(
                    message.format(election=election_name)
                )
            # Check that that post actually exists:
            if not Post.objects.filter(slug=post_id).exists():
                message = _("An unknown post ID '{post_id}' was specified")
                raise forms.ValidationError(message.format(post_id=post_id))
            try:
                party_set = PartySet.objects.get(post__slug=post_id)
            except PartySet.DoesNotExist:
                message = _(
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
                message = _("You must specify a party for the {election}")
                raise forms.ValidationError(
                    message.format(election=election_name)
                )
        return cleaned_data


class NewPersonForm(BasePersonForm):
    def __init__(self, *args, **kwargs):
        from candidates.election_specific import shorten_post_label

        election = kwargs.pop("election", None)
        hidden_post_widget = kwargs.pop("hidden_post_widget", None)
        super().__init__(*args, **kwargs)

        election_data = Election.objects.get_by_slug(election)

        standing_field_kwargs = {
            "label": _("Standing in %s") % election_data.name,
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
            "label": _("Post in the {election}").format(
                election=election_data.name
            ),
            "max_length": 256,
        }
        if hidden_post_widget:
            post_field_kwargs["widget"] = forms.HiddenInput()
            post_field = StrippedCharField(**post_field_kwargs)
        else:
            post_field = forms.ChoiceField(
                label=_("Post in the {election}").format(
                    election=election_data.name
                ),
                required=False,
                choices=[("", "")]
                + sorted(
                    [
                        (post.slug, shorten_post_label(post.label))
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
            specific_party_set = PartySet.objects.get(post__slug=post_id)

        party_registers_for_election = set(
            election_data.postextraelection_set.annotate(
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
                label=_("Party in {election} ({register})").format(
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
                    label=_(
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
        label=_("Source of information ({0})").format(settings.SOURCE_HINTS),
        max_length=512,
        error_messages={
            "required": _("You must indicate how you know about this candidate")
        },
        widget=forms.TextInput(
            attrs={
                "required": "required",
                "placeholder": _("How you know about this candidate"),
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
        from candidates.election_specific import shorten_post_label

        election = election_data.slug
        self.fields["standing_" + election] = forms.ChoiceField(
            label=_("Standing in %s") % election_data.name,
            choices=BasePersonForm.STANDING_CHOICES,
            widget=forms.Select(attrs={"class": "standing-select"}),
        )
        self.fields["constituency_" + election] = forms.ChoiceField(
            label=_("Constituency in %s") % election_data.name,
            required=False,
            choices=[("", "")]
            + sorted(
                [
                    (post.slug, shorten_post_label(post.label))
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
                label=_("Party in {election} ({party_set_name})").format(
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
                    label=_(
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
                postextraelection__membership__person=self.initial["person"]
            )
            .future()
            .order_by("-election_date")
        )
        # The fields on this form depends on how many elections are
        # going on at the same time. (FIXME: this might be better done
        # with formsets?)
        self.add_elections_fields(self.elections_with_fields)

    source = StrippedCharField(
        label=_("Source of information for this change ({0})").format(
            settings.SOURCE_HINTS
        ),
        max_length=512,
        error_messages={
            "required": _("You must indicate how you know about this candidate")
        },
        widget=forms.TextInput(
            attrs={
                "required": "required",
                "placeholder": _("How you know about this candidate"),
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

        cleaned_data = super().clean()
        return self.check_party_and_constituency_are_selected(cleaned_data)


class OtherNameForm(forms.ModelForm):
    class Meta:
        model = OtherName
        fields = ("name", "note", "start_date", "end_date")
        labels = {}
        help_texts = {
            "start_date": _(
                "(Optional) The date from which this name would be used"
            ),
            "end_date": _(
                "(Optional) The date when this name stopped being used"
            ),
        }

    source = StrippedCharField(
        label=_("Source"),
        help_text=_(
            "Please indicate how you know that this is a valid alternative name"
        ),
        max_length=512,
    )
