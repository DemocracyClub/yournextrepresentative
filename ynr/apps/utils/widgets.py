"""
For storing custom Django form widgets
"""
from django.forms.widgets import Select


class SelectWithAttrs(Select):
    """
    Subclass of Django's select widget that allows passing attrs to each item

    For example, to diable a single option, pass:

    choices=[(value, {'label': 'option label', 'disabled': True})]
    """

    def create_option(
        self, name, value, label, selected, index, subindex=None, attrs=None
    ):
        if type(label) == dict:
            label_text = label.pop("label")
        else:
            label_text = label
        option = super().create_option(
            name, value, label_text, selected, index, subindex=None, attrs=None
        )
        option["attrs"].update(label)
        return option
