from django import forms
from django.contrib.sites.models import Site
from django.core.exceptions import ValidationError

from candidates.models import Ballot
from people.forms.forms import AddElectionFieldsMixin, StrippedCharField


class UserTermsAgreementForm(forms.Form):

    assigned_to_dc = forms.BooleanField(required=False)
    next_path = StrippedCharField(max_length=512, widget=forms.HiddenInput())

    def clean_assigned_to_dc(self):
        assigned_to_dc = self.cleaned_data["assigned_to_dc"]
        if not assigned_to_dc:
            message = (
                "You can only edit data on {site_name} if you agree to "
                "this copyright assignment."
            ).format(site_name=Site.objects.get_current().name)
            raise ValidationError(message)
        return assigned_to_dc


class ToggleLockForm(forms.ModelForm):

    hashed_memberships = forms.CharField(
        widget=forms.HiddenInput, required=False
    )
    lock = forms.CharField(widget=forms.HiddenInput(), required=False)
    candidates_locked = forms.HiddenInput()

    class Meta:
        model = Ballot
        fields = ("candidates_locked",)

    def clean(self):
        if self.cleaned_data.get("lock") == "lock":
            if (
                self.cleaned_data["hashed_memberships"]
                != self.instance.hashed_memberships
            ):
                raise ValidationError(
                    "Someone changed the ballot since loading, please recheck"
                )

            self.cleaned_data["candidates_locked"] = True
        else:
            self.cleaned_data[
                "candidates_locked"
            ] = not self.instance.candidates_locked
        return self.cleaned_data


class ConstituencyRecordWinnerForm(forms.Form):
    person_id = StrippedCharField(
        label="Person ID", max_length=256, widget=forms.HiddenInput()
    )
    source = StrippedCharField(
        label="Source of information that they won", max_length=512
    )


class SingleElectionForm(AddElectionFieldsMixin, forms.Form):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        election_data = kwargs["initial"]["election"]
        user = kwargs["initial"]["user"]

        self.fields["extra_election_id"] = forms.CharField(
            max_length=256,
            widget=forms.HiddenInput(),
            initial=election_data.slug,
        )

        self.add_election_fields(election_data, user=user)
