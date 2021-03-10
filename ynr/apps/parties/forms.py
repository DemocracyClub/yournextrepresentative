from django import forms
from django.core.exceptions import ValidationError

from parties.models import Party


class PartyIdentifierInput(forms.CharField):
    def clean(self, value):
        if not value:
            return value
        try:
            return (
                Party.objects.current().get(ec_id__iexact=value.strip()).ec_id
            )
        except Party.DoesNotExist:
            raise ValidationError(
                f"'{value}' is not a current party " f"identifier"
            )


class PartySelectField(forms.MultiWidget):
    def __init__(self, choices, attrs=None):
        widgets = [forms.Select(choices=choices), forms.TextInput()]
        super().__init__(widgets, attrs)

    def decompress(self, value):
        if value:
            return value
        else:
            return ["", ""]


class PartyIdentifierField(forms.MultiValueField):
    def compress(self, data_list):
        if data_list:
            return data_list
        return None

    def __init__(self, *args, **kwargs):
        choices = Party.objects.default_party_choices()

        fields = (
            forms.ChoiceField(required=False, choices=choices),
            PartyIdentifierInput(required=False),
        )
        self.widget = PartySelectField(choices=choices)
        super().__init__(fields, *args, **kwargs)

    def clean(self, value):
        value = super().clean(value)
        if not any(value):
            return value
        # Always return the value from the char field if it exists, else the
        # select
        return self.to_python([v for v in value if v][-1])

    def to_python(self, value):
        if not value:
            return value
        return Party.objects.get(ec_id=value)
