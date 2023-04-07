from django import forms
from django.core.exceptions import ValidationError
from django.db.models import Prefetch
from django.utils.safestring import SafeText, mark_safe

from elections.models import Election
from parties.forms import (
    PartyIdentifierField,
    PopulatePartiesMixin,
    PreviousPartyAffiliationsField,
)
from people.forms.fields import BallotInputWidget, ValidBallotField
from search.utils import search_person_by_name
from official_documents.models import OfficialDocument
from parties.models import PartyDescription, Party
from popolo.models import Membership


class BaseBulkAddFormSet(forms.BaseFormSet):
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

    def clean(self):
        if (
            not self.initial_form_count()
            and self.ballot.membership_set.exists()
        ):
            # No extra forms exist, meaning no new people were added
            return super().clean()
        if hasattr(self, "cleaned_data"):
            if not any(self.cleaned_data):
                if not self.ballot.membership_set.exists():
                    raise ValidationError(
                        "At least one person required on this ballot"
                    )

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


class BaseBulkAddReviewFormSet(BaseBulkAddFormSet):
    def suggested_people(self, person_name):
        if person_name:
            qs = search_person_by_name(
                person_name, synonym=True
            ).prefetch_related(
                Prefetch(
                    "memberships",
                    queryset=Membership.objects.select_related(
                        "party",
                        "ballot",
                        "ballot__election",
                        "ballot__election__organization",
                    ),
                ),
            )
            return qs[:5]

    def format_value(
        self,
        suggestion,
        new_party=None,
        new_election: Election = None,
        new_name=None,
    ):
        """
        Turn the whole form in to a value string
        """
        name = suggestion.name
        if name == new_name:
            name = mark_safe(f"<strong>{name}</strong>")
        suggestion_dict = {"name": name, "object": suggestion}

        candidacies = (
            suggestion.memberships.select_related(
                "ballot__post", "ballot__election", "party"
            )
            .prefetch_related(
                Prefetch(
                    "ballot__officialdocument_set",
                    queryset=OfficialDocument.objects.filter(
                        document_type=OfficialDocument.NOMINATION_PAPER
                    ).order_by("-modified"),
                ),
            )
            .order_by("-ballot__election__election_date")[:3]
        )

        if candidacies:
            suggestion_dict["previous_candidacies"] = []

        for candidacy in candidacies:
            party = candidacy.party
            party_str = f"{party.name}"
            if new_party == party.ec_id:
                party_str = f"<strong>{party.name}</strong>"

            election = candidacy.ballot.election
            election_str = f"{election.name}"
            if new_election.organization == election.organization:
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
            suggestion_dict["previous_candidacies"].append(SafeText(text))

        return [suggestion.pk, suggestion_dict]

    def add_fields(self, form, index):
        super().add_fields(form, index)
        if not form["name"].value():
            return
        suggestions = self.suggested_people(form["name"].value())

        CHOICES = [("_new", "Add new person")]
        if suggestions:
            CHOICES += [
                self.format_value(
                    suggestion,
                    new_party=form.initial.get("party"),
                    new_election=self.ballot.election,
                    new_name=form.initial.get("name"),
                )
                for suggestion in suggestions
            ]
        form.fields["select_person"] = forms.ChoiceField(
            choices=CHOICES, widget=forms.RadioSelect()
        )
        form.fields["select_person"].initial = "_new"

        form.fields["party"] = forms.CharField(
            widget=forms.HiddenInput(
                attrs={"readonly": "readonly", "class": "party-select"}
            ),
            required=False,
        )

    def clean(self):
        errors = []
        if not hasattr(self, "ballot"):
            return super().clean()

        if self.ballot.candidates_locked:
            raise ValidationError(
                "Candidates have already been locked for this ballot"
            )

        for form_data in self.cleaned_data:

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
    name = forms.CharField(
        label="Name (style: Ali Smith, not SMITH Ali)",
        required=True,
        widget=forms.TextInput(
            attrs={"class": "person_name", "spellcheck": "false"}
        ),
    )
    ballot = ValidBallotField(
        widget=BallotInputWidget(attrs={"type": "hidden"})
    )


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

    def has_changed(self, *args, **kwargs):
        if "name" not in self.changed_data:
            return False
        else:
            return super().has_changed(*args, **kwargs)

    def clean(self):
        if (
            not self.cleaned_data["ballot"].is_welsh_run
            and self.cleaned_data["previous_party_affiliations"]
        ):
            raise ValidationError(
                "Previous party affiliations are invalid for this ballot"
            )
        return super().clean()


class ReviewSinglePersonNameOnlyForm(forms.Form):
    def __init__(self, *args, **kwargs):
        kwargs.pop("party_choices", None)
        super().__init__(*args, **kwargs)

    name = forms.CharField(
        required=False, widget=forms.HiddenInput(attrs={"readonly": "readonly"})
    )


class ReviewSinglePersonForm(ReviewSinglePersonNameOnlyForm):
    source = forms.CharField(
        required=False, widget=forms.HiddenInput(attrs={"readonly": "readonly"})
    )
    party_description = forms.ModelChoiceField(
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
    QuickAddSinglePersonForm, extra=15, formset=BulkAddFormSet, can_delete=True
)


BulkAddReviewNameOnlyFormSet = forms.formset_factory(
    ReviewSinglePersonNameOnlyForm, extra=0, formset=BaseBulkAddReviewFormSet
)

BulkAddReviewFormSet = forms.formset_factory(
    ReviewSinglePersonForm, extra=0, formset=BaseBulkAddReviewFormSet
)


class BaseBulkAddByPartyFormset(forms.BaseFormSet):
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
    NameOnlyPersonForm,
    extra=6,
    formset=BaseBulkAddByPartyFormset,
    can_delete=False,
)


class PartyBulkAddReviewFormSet(BaseBulkAddReviewFormSet):
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
    ReviewSinglePersonNameOnlyForm, extra=0, formset=PartyBulkAddReviewFormSet
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

        registers = set([p.upper() for p in party_set_qs])
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
        if not len([v for v in form_data.values() if v]) == 1:
            self.cleaned_data = {}
            raise forms.ValidationError("Select one and only one party")

        form_data["party"] = [v for v in form_data.values() if v][0]


class AddByPartyForm(forms.Form):

    source = forms.CharField(required=True)


class DeleteRawPeopleForm(forms.Form):

    ballot_paper_id = forms.CharField(required=True, widget=forms.HiddenInput)
