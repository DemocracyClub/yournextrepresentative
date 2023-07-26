"""
For storing custom Django form widgets
"""
from django.forms.widgets import Select, TextInput


class SelectWithAttrs(Select):
    """
    Subclass of Django's select widget that allows passing attrs to each item

    For example, to disable a single option, pass:

    choices=[(value, {'label': 'option label', 'disabled': True})]
    """

    def create_option(
        self, name, value, label, selected, index, subindex=None, attrs=None
    ):
        if type(label) == dict:
            label = dict(label)
            label_text = label.pop("label")
        else:
            label_text = label
        option = super().create_option(
            name, value, label_text, selected, index, subindex=None, attrs=None
        )
        option["attrs"].update(label)
        return option


class DCNumberInput(TextInput):
    """
    An input widget for entering numbers that isn't an input `type=number`.

    For more on why we do this, see this GDS post:

    https://technology.blog.gov.uk/2020/02/24/why-the-gov-uk-design-system-team-changed-the-input-type-for-numbers/

    """

    def build_attrs(self, base_attrs, extra_attrs=None):
        attrs = super().build_attrs(base_attrs, extra_attrs)
        attrs.update(
            {
                "inputmode": "numeric",
                "pattern": r"[0-9\s\.]*",
                "oninvalid": "this.setCustomValidity('Enter a number')",
            }
        )
        return attrs
