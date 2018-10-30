from django import forms
from django.contrib.sites.models import Site
from django.core.exceptions import ValidationError
from django.utils.translation import ugettext_lazy as _

from people.forms import StrippedCharField, AddElectionFieldsMixin


class UserTermsAgreementForm(forms.Form):

    assigned_to_dc = forms.BooleanField(required=False)
    next_path = StrippedCharField(max_length=512, widget=forms.HiddenInput())

    def clean_assigned_to_dc(self):
        assigned_to_dc = self.cleaned_data["assigned_to_dc"]
        if not assigned_to_dc:
            message = _(
                "You can only edit data on {site_name} if you agree to "
                "this copyright assignment."
            ).format(site_name=Site.objects.get_current().name)
            raise ValidationError(message)
        return assigned_to_dc


class ToggleLockForm(forms.Form):
    lock = forms.BooleanField(required=False, widget=forms.HiddenInput())
    post_id = StrippedCharField(max_length=256, widget=forms.HiddenInput())


class ConstituencyRecordWinnerForm(forms.Form):
    person_id = StrippedCharField(
        label=_("Person ID"), max_length=256, widget=forms.HiddenInput()
    )
    source = StrippedCharField(
        label=_("Source of information that they won"), max_length=512
    )


class SingleElectionForm(AddElectionFieldsMixin, forms.Form):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        election_data = kwargs["initial"]["election"]

        self.fields["extra_election_id"] = forms.CharField(
            max_length=256,
            widget=forms.HiddenInput(),
            initial=election_data.slug,
        )

        self.add_election_fields(election_data)
