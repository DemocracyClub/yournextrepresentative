from django import forms
from django.core.exceptions import ValidationError
from duplicates.models import DuplicateSuggestion


class DuplicateSuggestionForm(forms.ModelForm):
    class Meta:
        model = DuplicateSuggestion
        fields = ["other_person", "suggestion_reason"]
        labels = {"suggestion_reason": "Reason"}
        widgets = {
            "other_person": forms.HiddenInput(),
            "suggestion_reason": forms.Textarea(
                attrs={
                    "placeholder": "Please explain why you think these two people are duplicates",
                    "rows": 3,
                    "required": "",
                }
            ),
        }
        error_messages = {
            "other_person": {
                "invalid_choice": "The other person ID provided was invalid",
                "required": "Other person ID was not provided",
            },
            "suggestion_reason": {
                "required": "Reason for suggesting duplicate was not provided"
            },
        }

    def __init__(self, *args, **kwargs):
        person = kwargs.pop("person")
        user = kwargs.pop("user")
        require_reason = kwargs.pop("require_reason", True)
        super().__init__(*args, **kwargs)
        self.instance.person = person
        self.instance.user = user
        # The model field allows blank for legacy data, but new
        # suggestions submitted via this form should always include a
        # reason. The initial GET request (used to check the other person
        # ID before the reason has been entered on the review page) opts
        # out of this by passing require_reason=False.
        self.fields["suggestion_reason"].required = require_reason

    def clean(self):
        cleaned_data = super().clean()
        other_person = cleaned_data.get("other_person")

        if not other_person:
            return cleaned_data

        if self.instance.person.pk == other_person.pk:
            msg = f"You can't suggest a duplicate person ({self.instance.person.pk}) with themself ({other_person.pk})"
            self.add_error(field="other_person", error=msg)

        existing_suggestion = (
            DuplicateSuggestion.objects.for_both_people(
                person=self.instance.person, other_person=other_person
            )
            .open()
            .first()
        )
        if not existing_suggestion:
            return cleaned_data

        raise ValidationError(
            "A suggestion between these people is already open"
        )


class RejectionForm(forms.ModelForm):
    class Meta:
        model = DuplicateSuggestion
        fields = ["rejection_reasoning"]
        labels = {"rejection_reasoning": "Reason"}
        widgets = {
            "rejection_reasoning": forms.Textarea(
                attrs={
                    "placeholder": "Please explain your reasons for rejecting this suggestion"
                }
            )
        }

    def save(self, commit=True):
        """
        This is a rejection form so alwasy set status to NOT_DUPLICATE before
        saving
        """
        self.instance.status = DuplicateSuggestion.NOT_DUPLICATE
        return super().save(commit=commit)
