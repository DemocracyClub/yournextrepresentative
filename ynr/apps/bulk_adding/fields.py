from django import forms
from people.models import PersonIdentifier


class PersonIdentifierWidget(forms.MultiWidget):
    template_name = "bulk_add/includes/person_identifier_multiwidget.html"

    def __init__(self, *args, **kwargs):
        super().__init__(
            widgets=[
                forms.TextInput(),
                forms.Select(
                    choices=[("", "Select an option")]
                    + PersonIdentifier.objects.select_choices()[1:],
                ),
            ],
            **kwargs,
        )

    def decompress(self, value):
        # TODO: Turn single value back into list of two values
        return [None, None]


class PersonIdentifierField(forms.MultiValueField):
    def __init__(self, **kwargs):
        fields = (
            forms.CharField(
                required=True,
                error_messages={
                    "incomplete": "Please enter a social media link",
                },
            ),
            forms.ChoiceField(
                required=True,
                error_messages={
                    "incomplete": "Please select a link type",
                },
                choices=[("", "Select an option")]
                + PersonIdentifier.objects.select_choices()[1:],
            ),
        )
        widget = PersonIdentifierWidget()

        super().__init__(
            fields=fields,
            require_all_fields=False,
            widget=widget,
            **kwargs,
        )

    def compress(self, data_list):
        # TODO:
        # Validations
        # if valid, create single value
        return " ".join(data_list)
