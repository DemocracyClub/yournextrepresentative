from django import forms


from .models import PersonTask


class PersonTaskForm(forms.ModelForm):
    class Meta:
        model = PersonTask
        fields = ("person", "task_field")

        widgets = {
            "person": forms.HiddenInput(),
            "task_field": forms.HiddenInput(),
        }

    def save(self, *args, **kwargs):
        # log_not_found
        raise ValueError()
