from bulk_adding.fields import (
    PersonIdentifierFieldSet,
    PersonSuggestionField,
    PersonSuggestionRadioSelect,
)
from django import forms
from django.core.exceptions import ValidationError
from django.db.models import (
    CharField,
    Exists,
    IntegerField,
    OuterRef,
    Prefetch,
    Value,
)
from parties.forms import (
    PartyIdentifierField,
    PopulatePartiesMixin,
    PreviousPartyAffiliationsField,
)
from parties.models import Party, PartyDescription
from people.forms.fields import (
    BallotInputWidget,
    StrippedCharField,
    ValidBallotField,
)
from people.helpers import clean_biography, clean_birth_date
from popolo.models import Membership
from search.utils import search_person_by_name


class BaseBulkAddFormSet(forms.BaseFormSet):
    renderer = None

    def __init__(self, *args, **kwargs):
        if "source" in kwargs:
            self.source = kwargs["source"]
            del kwargs["source"]

        if "ballot" in kwargs:
            self.ballot = kwargs["ballot"]
            del kwargs["ballot"]

        super().__init__(*args, **kwargs)

    def add_fields(self, form, index):
        super().add_fields(form, index)
        form.initial["ballot"] = self.ballot.ballot_paper_id

        if hasattr(self, "source"):
            form.fields["source"].initial = self.source
            form.fields["source"].widget = forms.HiddenInput()

        if self.ballot.election.party_lists_in_use:
            form.fields["party_list_position"] = forms.IntegerField(
                label="Position in party list ('1' for first, '2' for second, etc.)",
                min_value=1,
                # Not required here, but we'll validate it later
                required=False,
                initial=None,
                widget=forms.NumberInput(attrs={"class": "party-position"}),
            )

    def clean(self):
        if (
            not self.initial_form_count()
            and self.ballot.membership_set.exists()
        ):
            # No extra forms exist, meaning no new people were added
            return super().clean()

        # Check if any forms have data
        has_data = any(
            form.is_valid()
            and form.cleaned_data
            and not form.cleaned_data.get("DELETE", False)
            for form in self.forms
        )

        if not has_data and not self.ballot.membership_set.exists():
            raise ValidationError("At least one person required on this ballot")

        return super().clean()


class BulkAddFormSet(BaseBulkAddFormSet):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.parties = Party.objects.register(
            self.ballot.post.party_set.slug.upper()
        ).default_party_choices(extra_party_ids=self.initial_party_ids)
        self.previous_party_affiliations_choices = (
            self.get_previous_party_affiliations_choices()
        )

    def total_form_count(self) -> int:
        """
        Base the additional fields on the seats contested multiplied
        by a sensible default.

        This is to prevent adding loads of additional fields if not needed.
        """

        form_counts = []

        seats_contested = self.ballot.winner_count
        # 3.5 is the average number of candidates per seat, historically, but
        # let's round that up to 4. Then multiply by the seats contested for
        # this ballot
        form_counts.append(int(seats_contested * 4))

        if self.is_bound:
            form_counts.append(super().total_form_count())

        if hasattr(self.ballot, "raw_people"):
            form_counts.append(len(self.ballot.rawpeople.textract_data))

        form_counts.append(self.ballot.membership_count)
        return max(form_counts) + 1

    def get_form_kwargs(self, index):
        kwargs = super().get_form_kwargs(index)
        kwargs["party_choices"] = self.parties
        kwargs[
            "previous_party_affiliations_choices"
        ] = self.previous_party_affiliations_choices
        return kwargs

    @property
    def initial_party_ids(self):
        """
        Returns a list of any party ID's that are included in initial data
        """
        if self.initial is None:
            return []
        return [d.get("party")[0].split("__")[0] for d in self.initial]

    def get_previous_party_affiliations_choices(self):
        """
        Return choices for previous_party_affilations field. By getting these on
        the formset and passing to the form, it saves the query for every
        individual form
        """
        if not self.ballot.is_welsh_run:
            return []

        parties = Party.objects.register("GB").active_in_last_year(
            date=self.ballot.election.election_date
        )
        return parties.values_list("ec_id", "name")


class BaseBulkAddReconcileFormSet(BaseBulkAddFormSet):
    def suggested_people(
        self,
        person_name,
        new_party,
        new_election,
        new_name,
        ballot=None,
    ):
        """
        At a basic level, use the person search system to find existing people
        who might be the same as the values submitted via bulk adding.

        Normal weightings apply, with two additional weights:

        1. If there's a match for a person that's already listed on the ballot
           then that gets pulled to the top of the list.
        2. People with the same party as the new person are weighted higher.
           Party matching like this isn't going to be right in all cases
           (people switch party) but it will be more useful than name alone
           more of the time

        These two additional weights combined should catch the 'this candidate
        is already listed on the ballot' case, or at least it's a simpler
        UX than simply asking users to de-duplicate existing people on the
        previous form.
        """
        if not person_name:
            return None

        org_id = (
            new_election.organization.pk
            if new_election and new_election.organization
            else None
        )
        annotations = {
            "new_party": Value(new_party, output_field=CharField()),
            "new_organisation": Value(
                org_id,
                output_field=IntegerField(),
            ),
            "new_name": Value(new_name, output_field=CharField()),
        }

        qs = (
            search_person_by_name(person_name, synonym=True)
            .prefetch_related(
                Prefetch(
                    "memberships",
                    queryset=Membership.objects.select_related(
                        "party",
                        "ballot",
                        "ballot__election",
                        "ballot__election__organization",
                        "ballot__post",
                        "ballot__sopn",
                    ).order_by("-ballot__election__election_date"),
                ),
                "other_names",
            )
            .annotate(**annotations)
        )

        order_by = []

        if ballot:
            # Annotate the QS with on_ballot: True if the matched person
            # exists on a given ballot.
            on_ballot = Exists(
                Membership.objects.filter(person=OuterRef("pk"), ballot=ballot)
            )
            qs = qs.annotate(on_ballot=on_ballot)
            order_by.append("-on_ballot")

        if new_party:
            # Annotate the QS with same_party: True if the person has a
            # candidacy with the same party as the given one
            same_party = Exists(
                Membership.objects.filter(
                    person=OuterRef("pk"), party__ec_id=new_party
                )
            )
            qs = qs.annotate(same_party=same_party)
            order_by.append("-same_party")

        if order_by:
            qs = qs.order_by(*order_by, "-rank", "membership_count")

        return qs[:5]

    def add_fields(self, form, index):
        super().add_fields(form, index)
        if not form["name"].value():
            return
        # On POST, form.initial is empty; fall back to the submitted POST data
        party_id = form.initial.get("party_id") or form.data.get(
            form.add_prefix("party_id")
        )
        suggestions = self.suggested_people(
            form["name"].value(),
            new_party=party_id,
            new_election=self.ballot.election,
            new_name=form.initial.get("name"),
            ballot=self.ballot,
        )

        form.fields["select_person"] = PersonSuggestionField(
            suggestions=suggestions,
            new_name=form.initial.get("name"),
            widget=PersonSuggestionRadioSelect,
        )

        # If reconciled data exists, use that as the initial values
        previous_selection = form.initial.get("select_person")
        if previous_selection and form.fields["select_person"].valid_value(
            str(previous_selection)
        ):
            form.fields["select_person"].initial = str(previous_selection)

        form.fields["party_id"] = forms.CharField(
            widget=forms.HiddenInput(
                attrs={"readonly": "readonly", "class": "party-select"}
            ),
            required=False,
        )
        form.fields["sopn_last_name"] = StrippedCharField(
            widget=forms.HiddenInput(attrs={"readonly": "readonly"}),
            required=False,
        )
        form.fields["sopn_first_names"] = StrippedCharField(
            widget=forms.HiddenInput(attrs={"readonly": "readonly"}),
            required=False,
        )
        if self.ballot.election.party_lists_in_use:
            form.fields["party_list_position"] = forms.IntegerField(
                min_value=1, required=False, widget=forms.HiddenInput()
            )

    def clean(self):
        errors = []
        if not hasattr(self, "ballot"):
            return super().clean()

        if self.ballot.candidates_locked:
            raise ValidationError(
                "Candidates have already been locked for this ballot"
            )
        for form in self.forms:
            if not form.is_valid():
                continue
            form_data = form.cleaned_data
            if (
                "select_person" in form_data
                and form_data["select_person"] == "_new"
            ):
                continue
            qs = (
                Membership.objects.filter(ballot__election=self.ballot.election)
                .filter(person_id=form_data.get("select_person"))
                .exclude(ballot=self.ballot)
                .exclude(ballot__candidates_locked=True)
            )
            if qs.exists():
                errors.append(
                    forms.ValidationError(
                        "'{}' is marked as standing in another ballot for this "
                        "election. Check you're entering the correct "
                        "information for {}".format(
                            form_data["name"], self.ballot.post.label
                        )
                    )
                )
        if errors:
            raise forms.ValidationError(errors)
        return super().clean()


class NameOnlyPersonForm(forms.Form):
    name = StrippedCharField(
        label="Name (style: Ali McKay Smith not SMITH Ali McKay)",
        required=True,
        widget=forms.TextInput(
            attrs={"class": "person_name", "spellcheck": "false"}
        ),
    )
    ballot = ValidBallotField(
        widget=BallotInputWidget(attrs={"type": "hidden"})
    )
    sopn_last_name = StrippedCharField(
        widget=forms.HiddenInput(attrs={"readonly": "readonly"}),
        required=False,
    )
    sopn_first_names = StrippedCharField(
        widget=forms.HiddenInput(attrs={"readonly": "readonly"}),
        required=False,
    )


class BulkAddByPartyForm(NameOnlyPersonForm):
    biography = StrippedCharField(
        label="Statement to Voters",
        required=False,
        widget=forms.Textarea(
            attrs={"class": "person_biography"},
        ),
    )
    gender = StrippedCharField(
        label="Gender (e.g. “male”, “female”)", required=False
    )
    birth_date = forms.CharField(
        label="Year of birth (a four digit year)",
        required=False,
        widget=forms.NumberInput,
    )
    person_identifiers = PersonIdentifierFieldSet(
        label="Links and social media",
        required=False,
    )

    def clean_biography(self):
        bio = self.cleaned_data["biography"]
        return clean_biography(bio)

    def clean_birth_date(self):
        bd = self.cleaned_data["birth_date"]
        return clean_birth_date(bd)


class QuickAddSinglePersonForm(PopulatePartiesMixin, NameOnlyPersonForm):
    source = forms.CharField(required=True)
    party = PartyIdentifierField()
    previous_party_affiliations = PreviousPartyAffiliationsField()

    def __init__(self, **kwargs):
        previous_party_affiliations_choices = kwargs.pop(
            "previous_party_affiliations_choices", []
        )
        super().__init__(**kwargs)
        self.fields[
            "previous_party_affiliations"
        ].choices = previous_party_affiliations_choices

    def full_clean(self):
        """
        Consider a form as empty if there's no name.

        Remove any other errors from other fields.
        """
        name_key = self.add_prefix("name")
        if self.is_bound and not (self.data.get(name_key, "")).strip():
            self._errors = forms.utils.ErrorDict()
            self.cleaned_data = {}
            return
        super().full_clean()

    def has_changed(self, *args, **kwargs):
        name_key = self.add_prefix("name")
        if not (self.data.get(name_key) or "").strip():
            return False
        return super().has_changed(*args, **kwargs)

    def clean_party_list_position(self, *args, **kwargs):
        if self.cleaned_data["party"]["party_id"] == "ynmp-party:2":
            return None
        if not self.cleaned_data["party_list_position"]:
            raise ValidationError("List position required")
        return self.cleaned_data["party_list_position"]

    def clean(self):
        if (
            not self.cleaned_data["ballot"].is_welsh_run
            and self.cleaned_data["previous_party_affiliations"]
        ):
            raise ValidationError(
                "Previous party affiliations are invalid for this ballot"
            )

        return super().clean()


class ReconcileSinglePersonNameOnlyForm(forms.Form):
    def __init__(self, *args, **kwargs):
        kwargs.pop("party_choices", None)
        super().__init__(*args, **kwargs)

    name = StrippedCharField(
        required=False, widget=forms.HiddenInput(attrs={"readonly": "readonly"})
    )


class ReviewBulkAddByPartyForm(ReconcileSinglePersonNameOnlyForm):
    biography = StrippedCharField(
        required=False, widget=forms.HiddenInput(attrs={"readonly": "readonly"})
    )
    gender = StrippedCharField(
        required=False, widget=forms.HiddenInput(attrs={"readonly": "readonly"})
    )
    birth_date = forms.CharField(
        required=False, widget=forms.HiddenInput(attrs={"readonly": "readonly"})
    )
    person_identifiers = forms.CharField(
        required=False,
        widget=forms.HiddenInput(
            attrs={"readonly": "readonly"},
        ),
    )


class ReconcileSinglePersonForm(ReconcileSinglePersonNameOnlyForm):
    source = forms.CharField(
        required=False, widget=forms.HiddenInput(attrs={"readonly": "readonly"})
    )
    description_id = forms.ModelChoiceField(
        required=False,
        widget=forms.HiddenInput(),
        queryset=PartyDescription.objects.all(),
    )
    party_description_text = forms.CharField(
        required=False, widget=forms.HiddenInput()
    )
    previous_party_affiliations = forms.CharField(
        required=False, widget=forms.HiddenInput()
    )


BulkAddFormSetFactory = forms.formset_factory(
    QuickAddSinglePersonForm, extra=0, formset=BulkAddFormSet, can_delete=True
)


BulkAddReconcileNameOnlyFormSet = forms.formset_factory(
    ReconcileSinglePersonNameOnlyForm,
    extra=0,
    formset=BaseBulkAddReconcileFormSet,
)

BulkAddReconcileFormSet = forms.formset_factory(
    ReconcileSinglePersonForm, extra=0, formset=BaseBulkAddReconcileFormSet
)


class BaseBulkAddByPartyFormset(forms.BaseFormSet):
    renderer = None

    def __init__(self, *args, **kwargs):
        self.ballot = kwargs["ballot"]
        kwargs["prefix"] = self.ballot.pk
        self.extra = self.ballot.winner_count
        del kwargs["ballot"]

        super().__init__(*args, **kwargs)

    def add_fields(self, form, index):
        super().add_fields(form, index)
        if self.ballot.election.party_lists_in_use:
            form.fields["party_list_position"] = forms.IntegerField(
                label="Position in party list ('1' for first, '2' for second, etc.)",
                min_value=1,
                required=False,
                initial=index + 1,
                widget=forms.NumberInput(attrs={"class": "party-position"}),
            )

        if self.ballot.candidates_locked:
            for name, field in form.fields.items():
                field.disabled = True
                form.fields[name] = field


BulkAddByPartyFormset = forms.formset_factory(
    BulkAddByPartyForm,
    extra=6,
    formset=BaseBulkAddByPartyFormset,
    can_delete=False,
)


class PartyBulkAddReviewFormSet(BaseBulkAddReconcileFormSet):
    def __init__(self, *args, **kwargs):
        self.ballot = kwargs["ballot"]
        kwargs["prefix"] = self.ballot.pk
        self.extra = self.ballot.winner_count
        del kwargs["ballot"]

        super().__init__(*args, **kwargs)

    def clean(self):
        """
        Use this method to prevent users from adding candidates to ballots
        that can't have candidates added to them, like locked or cancelled
        ballots
        """
        if self.ballot.candidates_locked:
            raise ValidationError("Cannot add candidates to a locked ballot")
        if self.ballot.cancelled:
            raise ValidationError(
                "Cannot add candidates to a cancelled election"
            )

    def add_fields(self, form, index):
        super().add_fields(form, index)
        if self.ballot.election.party_lists_in_use:
            form.fields["party_list_position"] = forms.IntegerField(
                min_value=1, required=False, widget=forms.HiddenInput()
            )


PartyBulkAddReviewNameOnlyFormSet = forms.formset_factory(
    ReviewBulkAddByPartyForm, extra=0, formset=PartyBulkAddReviewFormSet
)


class SelectPartyForm(forms.Form):
    def __init__(self, *args, **kwargs):
        election = kwargs.pop("election")
        super().__init__(*args, **kwargs)

        self.election = election
        party_set_qs = (
            election.ballot_set.all()
            .order_by("post__party_set")
            .values_list("post__party_set__slug", flat=True)
        )

        registers = {p.upper() for p in party_set_qs}
        for register in registers:
            choices = Party.objects.register(register).party_choices(
                include_description_ids=True
            )
            field = PartyIdentifierField(
                label=f"{register} parties", choices=choices
            )

            field.fields[0].choices = choices
            field.widget.attrs["data-party-register"] = register
            field.widget.attrs["register"] = register
            self.fields[f"party_{register}"] = field

    def clean(self):
        form_data = self.cleaned_data
        if len([v for v in form_data.values() if v]) != 1:
            raise forms.ValidationError("Select one and only one party")

        form_data["party"] = [v for v in form_data.values() if v][0]
        return form_data


class AddByPartyForm(forms.Form):
    source = forms.CharField(required=True)


class DeleteRawPeopleForm(forms.Form):
    ballot_paper_id = forms.CharField(required=True, widget=forms.HiddenInput)


class ConfirmCandidacyRemovalForm(forms.Form):
    """
    Shown on the bulk-add confirm page for existing candidacies that will be
    removed. The user must check a box next to every candidacy to be removed.
    """

    def __init__(self, *args, candidacies_to_remove=None, **kwargs):
        super().__init__(*args, **kwargs)
        for candidacy in candidacies_to_remove or []:
            field = forms.BooleanField(
                label=f"{candidacy.person.name} ({candidacy.party.name})",
                required=True,
                error_messages={
                    "required": f"You must confirm the removal of {candidacy.person.name} from this ballot"
                },
            )
            field.candidacy = candidacy
            self.fields[f"confirm_remove_{candidacy.pk}"] = field
