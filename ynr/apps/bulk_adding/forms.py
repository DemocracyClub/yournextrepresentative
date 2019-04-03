from django import forms
from django.db.models import Count
from django.core.exceptions import ValidationError
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

        if "ballot" in kwargs:
            self.ballot = kwargs["ballot"]
            del kwargs["ballot"]

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
            if self.initial:
                # If we have raw people with parties that wouldn't normally
                # be in the party list (beacuse they have no current
                # candidates yet) then we should manually add them,
                # so that the dropdown isn't empty.
                existing_ids = set(
                    [v[0][0] for k, v in form.fields["party"].choices if v]
                )
                extra_parties = set()
                for row in self.initial:
                    if row.get("party"):
                        party_id = row["party"].split("__")[0]
                        if party_id in existing_ids:
                            continue
                        extra_parties.add(party_id)
                party_qs = Party.objects.filter(
                    ec_id__in=extra_parties
                ).prefetch_related("descriptions")

                for party_obj in party_qs:
                    names = [(party_obj.ec_id, party_obj.format_name)]
                    for description in party_obj.descriptions.all():
                        names.append((party_obj.ec_id, description.description))
                    form.fields["party"].choices.extend(names)

            if "party" in getattr(form, "_hide", []):
                form.fields["party"].widget = forms.HiddenInput()

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
        suggestion_dict = {"name": name, "object": suggestion.object}

        candidacies = suggestion.object.memberships.select_related(
            "post", "party", "post_election__election"
        ).order_by("-post_election__election__election_date")[:3]

        if candidacies:
            suggestion_dict["previous_candidacies"] = []

        for candidacy in candidacies:
            text = """{election}: {post} – {party}""".format(
                post=candidacy.post.short_label,
                election=candidacy.post_election.election.name,
                party=candidacy.party.name,
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
                self.format_value(suggestion) for suggestion in suggestions
            ]
        form.fields["select_person"] = forms.ChoiceField(
            choices=CHOICES, widget=forms.RadioSelect()
        )
        form.fields["select_person"].initial = "_new"

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

    def has_changed(self, *args, **kwargs):
        if self.changed_data == ["source"] and not self["name"].data:
            return False
        else:
            return super().has_changed(*args, **kwargs)


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
    QuickAddSinglePersonForm,
    extra=15,
    formset=BaseBulkAddFormSet,
    can_delete=True,
)


BulkAddReviewNameOnlyFormSet = forms.formset_factory(
    ReviewSinglePersonNameOnlyForm, extra=0, formset=BaseBulkAddReviewFormSet
)

BulkAddReviewFormSet = forms.formset_factory(
    ReviewSinglePersonForm, extra=0, formset=BaseBulkAddReviewFormSet
)


class SelectAnythingChoiceField(forms.ChoiceField):
    """
    Because we don't always show all parties on the initial page load (we
    leave JavaScript to add the non-current parties sometimes), we need to
    ignore any input value for this field type. The next page will
    raise a 404 if the party isn't actually found, so there's no problem with
    ignoring validation here.
    """

    def validate(self, value):
        return True


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
            self.fields[
                "party_{}".format(register)
            ] = SelectAnythingChoiceField(
                required=False,
                choices=Party.objects.register(register).party_choices(
                    exclude_deregistered=True,
                    include_descriptions=False,
                    include_non_current=False,
                ),
                widget=forms.Select(
                    attrs={
                        "class": "party-select",
                        "show_load_more": 1,
                        "data-partyset": register,
                    }
                ),
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
