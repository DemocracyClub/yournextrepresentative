"""
For storing custom Django form widgets
"""

from dataclasses import dataclass
from typing import Optional

from django.forms.widgets import Select, TextInput


@dataclass
class ChoiceOptionWithContext:
    """
    A tiny wrapper for choices.

    This is needed to allow passing per-option attributes to each <option>
    element.

    Django 5+ assumed a dict or other mapping type should be converted into a
    opt group. This class allows passing richer data types to the
    `create_option` method of the `SelectWithAttrs` widget.
    """

    # Becomes the text label on the select
    label: str
    # Anything in this mapping is added to the HTML attributes
    attrs: Optional[dict] = None

    @classmethod
    def from_dict(cls, choice: dict):
        if isinstance(choice, str):
            return cls(label=choice)
        # Label is required
        label = choice.get("label")
        return cls(
            label=label, attrs={k: v for k, v in choice.items() if k != "label"}
        )


def choices_to_context_choices(choices):
    context_choices = []
    for choice in choices:
        value, choice_data = choice
        if isinstance(choice_data, dict):
            context_choices.append(
                (value, ChoiceOptionWithContext.from_dict(choice_data))
            )
        if isinstance(choice_data, list):
            sub_choices = []
            for sub_choice in choice_data:
                sub_choices.append(
                    (
                        sub_choice[0],
                        ChoiceOptionWithContext.from_dict(sub_choice[1]),
                    )
                )
            context_choices.append((value, sub_choices))
        if isinstance(choice_data, str):
            context_choices.append((value, choice_data))
    return context_choices


class SelectWithAttrs(Select):
    """
    Subclass of Django's select widget that allows passing attrs to each item

    For example, to disable a single option, pass:

    choices=[(value, {'label': 'option label', 'disabled': True})]
    """

    def create_option(
        self, name, value, label, selected, index, subindex=None, attrs=None
    ):
        if isinstance(label, ChoiceOptionWithContext):
            label_text = label.label
        else:
            label_text = label
        option = super().create_option(
            name, value, label_text, selected, index, subindex=None, attrs=None
        )
        if isinstance(label, ChoiceOptionWithContext):
            option["attrs"] = label.attrs

        return option


class DCIntegerInput(TextInput):
    """
    An input widget for entering numbers that isn't an input `type=number`.

    For more on why we do this, see this GDS post:

    https://technology.blog.gov.uk/2020/02/24/why-the-gov-uk-design-system-team-changed-the-input-type-for-numbers/

    """

    def build_attrs(self, base_attrs, extra_attrs=None):
        attrs = super().build_attrs(base_attrs, extra_attrs)
        attrs.update(
            {
                "pattern": r"[0-9\s\.]*",
                "oninvalid": "this.setCustomValidity('Enter a number')",
                "oninput": "this.setCustomValidity('');",
                "onchange": """
                if (this.value !== "") {
                    this.value = Math.round(this.value.replace(/\D/g, '')).toString()
                }
                """,
            }
        )
        return attrs


class DCPercentageInput(TextInput):
    def build_attrs(self, base_attrs, extra_attrs=None):
        attrs = super().build_attrs(base_attrs, extra_attrs)
        attrs.update(
            {
                "pattern": r"[0-9\s\.]*",
                "oninvalid": "this.setCustomValidity('Enter a percentage or a whole number')",
                "oninput": "this.setCustomValidity('');",
                "onchange": """
                let value = this.value.replace(",", ".");
                value = value.replace("%", "");
                value = value.trim();
                if (value !== "") {
                    value = parseFloat(value).toFixed(2).toString();
                }
                this.value = value;
            """,
            }
        )
        return attrs
