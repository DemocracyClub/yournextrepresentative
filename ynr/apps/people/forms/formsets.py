from django import forms
from django.forms import BaseInlineFormSet
from django.forms.formsets import DELETION_FIELD_NAME
from people.forms.forms import PersonIdentifierForm, PersonMembershipForm
from people.models import Person, PersonIdentifier
from popolo.models import Membership

PersonIdentifierFormsetFactory = forms.inlineformset_factory(
    Person,
    PersonIdentifier,
    form=PersonIdentifierForm,
    can_delete=True,
    widgets={
        "value_type": forms.Select(
            choices=[("", "Select an option")]
            + PersonIdentifier.objects.select_choices()[1:],
        )
    },
)


class MembershipFormSet(BaseInlineFormSet):
    def add_fields(self, form, index):
        super().add_fields(form, index)
        # Don't allow deleting locked ballots
        if form.instance.pk and form.instance.ballot.candidates_locked:
            del form.fields[DELETION_FIELD_NAME]

    def get_queryset(self):
        qs = super().get_queryset()
        return qs.filter(
            ballot__candidates_locked=False, ballot__election__current=True
        ).select_related("ballot", "ballot__election")

    def get_form_kwargs(self, index):
        kwargs = super().get_form_kwargs(index)
        kwargs["person"] = self.instance
        return kwargs

    def clean(self):
        # Reject adding the same person to two ballots from the same
        # election (e.g. two wards in the same council on the same date) -
        # that combination otherwise blew up downstream with a 500 (#2685).
        super().clean()
        seen_elections = {}
        for form in self.forms:
            if not form.cleaned_data:
                continue
            if form.cleaned_data.get(DELETION_FIELD_NAME):
                continue
            ballot = form.cleaned_data.get("ballot_paper_id")
            if not ballot:
                continue
            election_id = ballot.election_id
            other = seen_elections.get(election_id)
            if other is not None:
                form.add_error(
                    "ballot_paper_id",
                    "This person is already standing in another ballot "
                    "in the same election ({}); please remove one before "
                    "saving.".format(other.ballot_paper_id),
                )
            else:
                seen_elections[election_id] = ballot


PersonMembershipFormsetFactory = forms.inlineformset_factory(
    Person,
    Membership,
    form=PersonMembershipForm,
    formset=MembershipFormSet,
    # TODO: Prevent editing locked ballots here
    can_delete=True,
    extra=1,
)
