from data_exports.csv_fields import csv_fields
from data_exports.models import CSVDownloadReason
from django import forms


def extra_field_choices():
    choices = []
    for name, field in csv_fields.items():
        if not field.core:
            choices.append((name, name))
    return choices


def grouped_choices():
    groups = {}
    for name, field in csv_fields.items():
        if field.core:
            continue
        group_fields = groups.get(field.value_group, [])
        group_fields.append((name, field))
        groups[field.value_group] = group_fields
    return groups


class AdditionalFieldsForm(forms.Form):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for group in grouped_choices():
            self.fields[group] = forms.BooleanField(
                widget=forms.CheckboxInput, required=False
            )

    extra_fields = forms.MultipleChoiceField(
        choices=extra_field_choices,
        widget=forms.CheckboxSelectMultiple(),
        required=False,
    )


class CSVDownloadReasonForm(forms.ModelForm):
    class Meta:
        model = CSVDownloadReason
        exclude = ("user",)

    def __init__(self, *args, user=None, **kwargs):
        """
        Take a User. If the user is authenticated, remove email from the form.
        """
        super().__init__(*args, **kwargs)
        self.user = user

        if user and user.is_authenticated:
            self.fields.pop("email", None)
        else:
            self.fields["email"].required = False
            self.fields[
                "email"
            ].help_text = "(optional - please enter your email if you are happy to contacted by us if we have questions about your work)"
