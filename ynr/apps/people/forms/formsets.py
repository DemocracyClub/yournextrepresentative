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
            choices=PersonIdentifier.objects.select_choices()
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


PersonMembershipFormsetFactory = forms.inlineformset_factory(
    Person,
    Membership,
    form=PersonMembershipForm,
    formset=MembershipFormSet,
    # TODO: Prevent editing locked ballots here
    can_delete=True,
    extra=1,
)
