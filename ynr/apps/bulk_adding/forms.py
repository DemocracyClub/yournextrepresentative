from django import forms
from django.db.models import Count
from django.utils.safestring import SafeText
from django.utils.translation import ugettext_lazy as _

from candidates.views import search_person_by_name
from parties.models import Party


class BaseBulkAddFormSet(forms.BaseFormSet):
    def __init__(self, *args, **kwargs):
        if "parties" in kwargs:
            self.parties = kwargs["parties"]
            del kwargs["parties"]
        if "party_set" in kwargs:
            self.party_set_slug = kwargs["party_set"].slug
            del kwargs["party_set"]
        else:
            self.party_set_slug = None
        if "source" in kwargs:
            self.source = kwargs["source"]
            del kwargs["source"]
        super().__init__(*args, **kwargs)

    def add_fields(self, form, index):
        super().add_fields(form, index)
        if hasattr(self, "parties"):
            form.fields["party"] = forms.ChoiceField(
                choices=self.parties,
                widget=forms.Select(
                    attrs={
                        "class": "party-select",
                        "show_load_more": 1,
                        "data-partyset": self.party_set_slug,
                    }
                ),
            )

            if "party" in getattr(form, "_hide", []):
                form.fields["party"].widget = forms.HiddenInput()

        if hasattr(self, "source"):
            form.fields["source"].initial = self.source
            form.fields["source"].widget = forms.HiddenInput()


class BaseBulkAddReviewFormSet(BaseBulkAddFormSet):
    def suggested_people(self, person_name):
        if person_name:
            sqs = search_person_by_name(person_name)
            return sqs[:5]

    def format_value(self, suggestion):
        """
        Turn the whole form in to a value string
        """
        name = suggestion.name

        candidacy = (
            suggestion.object.memberships.select_related(
                "post", "party", "post_election__election"
            )
            .order_by("-post_election__election__election_date")
            .first()
        )
        if candidacy:
            name = """
                <strong>{name}</strong>
                    (previously stood in {post} in the {election} as a
                    {party} candidate)
                    """.format(
                name=name,
                post=candidacy.post.short_label,
                election=candidacy.post_election.election.name,
                party=candidacy.party.name,
            )
            name = SafeText(name)

        return [suggestion.pk, name]

    def add_fields(self, form, index):
        super().add_fields(form, index)
        if not form["name"].value():
            return
        suggestions = self.suggested_people(form["name"].value())

        CHOICES = [("_new", "Add new person")]
        if suggestions:
            CHOICES += [
                self.format_value(suggestion) for suggestion in suggestions
            ]
        form.fields["select_person"] = forms.ChoiceField(
            choices=CHOICES, widget=forms.RadioSelect()
        )

        if hasattr(self, "parties"):
            form.fields["party"] = forms.ChoiceField(
                choices=self.parties,
                widget=forms.HiddenInput(
                    attrs={"readonly": "readonly", "class": "party-select"}
                ),
                required=False,
            )


class NameOnlyPersonForm(forms.Form):
    name = forms.CharField(
        label=_("Name (style: Ali Smith, not SMITH Ali)"), required=True
    )


class QuickAddSinglePersonForm(NameOnlyPersonForm):
    source = forms.CharField(required=True)


class ReviewSinglePersonNameOnlyForm(forms.Form):
    name = forms.CharField(
        required=False, widget=forms.HiddenInput(attrs={"readonly": "readonly"})
    )


class ReviewSinglePersonForm(ReviewSinglePersonNameOnlyForm):
    source = forms.CharField(
        required=False, widget=forms.HiddenInput(attrs={"readonly": "readonly"})
    )
    party_description = forms.CharField(
        required=False, widget=forms.HiddenInput()
    )


BulkAddFormSet = forms.formset_factory(
    QuickAddSinglePersonForm, extra=15, formset=BaseBulkAddFormSet
)


BulkAddReviewNameOnlyFormSet = forms.formset_factory(
    ReviewSinglePersonNameOnlyForm, extra=0, formset=BaseBulkAddReviewFormSet
)

BulkAddReviewFormSet = forms.formset_factory(
    ReviewSinglePersonForm, extra=0, formset=BaseBulkAddReviewFormSet
)


class BulkAddByPartyFormset(forms.BaseFormSet):
    pass


class SelectPartyForm(forms.Form):
    def __init__(self, *args, **kwargs):

        election = kwargs.pop("election")
        super().__init__(*args, **kwargs)

        self.election = election
        party_set_qs = (
            election.postextraelection_set.all()
            .order_by("post__party_set")
            .values_list("post__party_set__slug", flat=True)
            .annotate(Count("post__party_set"))
        )

        registers = set([p.upper() for p in party_set_qs])
        for register in registers:
            self.fields["party_{}".format(register)] = forms.ChoiceField(
                required=False,
                choices=Party.objects.register(register).party_choices(
                    exclude_deregistered=True,
                    include_descriptions=False,
                    include_non_current=False,
                ),
                widget=forms.Select(attrs={"class": "party-select"}),
                label="{} Parties".format(register),
            )

    def clean(self):
        form_data = self.cleaned_data
        if not len([v for v in form_data.values() if v]) == 1:
            self.cleaned_data = {}
            raise forms.ValidationError("Select one and only one party")
        form_data["party"] = [v for v in form_data.values() if v][0]


class AddByPartyForm(forms.Form):

    source = forms.CharField(required=True)
