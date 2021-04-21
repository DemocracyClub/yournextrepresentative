from django import forms
from django.core.exceptions import ValidationError

from duplicates.models import DuplicateSuggestion


class DuplicateSuggestionForm(forms.ModelForm):
    class Meta:
        model = DuplicateSuggestion
        fields = ["other_person"]
        widgets = {"other_person": forms.HiddenInput()}
        error_messages = {
            "other_person": {
                "invalid_choice": "The other person ID provided was invalid",
                "required": "Other person ID was not provided",
            }
        }

    def __init__(self, *args, **kwargs):
        person = kwargs.pop("person")
        user = kwargs.pop("user")
        super().__init__(*args, **kwargs)
        self.instance.person = person
        self.instance.user = user

    def clean(self):
        cleaned_data = super().clean()
        other_person = cleaned_data.get("other_person")

        if not other_person:
            return cleaned_data

        if self.instance.person.pk == other_person.pk:
            msg = f"You can't suggested a duplicate person ({self.instance.person.pk}) with themself ({other_person.pk})"
            self.add_error(field="other_person", error=msg)

        existing_suggestion = DuplicateSuggestion.objects.for_both_people(
            person=self.instance.person, other_person=other_person
        ).first()
        if not existing_suggestion:
            return cleaned_data

        if existing_suggestion.open:
            raise ValidationError(
                "A suggestion between these people is already open"
            )

        if existing_suggestion.rejected:
            raise ValidationError(
                "A suggestion between these two people has already been checked and rejected as not duplicate"
            )
