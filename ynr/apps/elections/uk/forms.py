from django import forms
from django.core.exceptions import ValidationError

from elections.uk.geo_helpers import (
    BadPostcodeException,
    UnknownGeoException,
    get_ballots_from_postcode,
)


class PostcodeForm(forms.Form):
    q = forms.CharField(
        label="Enter a candidate name or postcode",
        max_length=200,
        widget=forms.TextInput(
            attrs={"placeholder": "Enter a name or postcode"}
        ),
    )

    def clean_q(self):
        postcode = self.cleaned_data["q"]
        try:
            # Check if this postcode is valid and
            # contained in a constituency. (If it's valid then the
            # result is cached, so this doesn't cause a double lookup.)
            get_ballots_from_postcode(postcode)
        except (UnknownGeoException, BadPostcodeException) as e:
            raise ValidationError(str(e))
        return postcode
