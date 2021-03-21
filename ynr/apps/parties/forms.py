from django import forms
from django.core.exceptions import ValidationError

from parties.models import Party
from people.forms.fields import BallotInputWidget
from utils.widgets import SelectWithAttrs


def party_and_description_dict_from_string(value):
    """
    Given an input string in the form of "party" or "party__description"
    return a dict containing party and description name, id and objects

    """
    if not value:
        return value
    if "__" in value:
        party_id, description_id = value.split("__")
    else:
        party_id = value
        description_id = None
    try:
        party = Party.objects.current().get(ec_id__iexact=party_id.strip())
        ret = {
            "party_obj": party,
            "party_id": party.ec_id,
            "party_name": party.name,
            "description_id": None,
            "description_obj": None,
            "description_text": None,
        }
        if description_id:
            description = party.descriptions.get(pk=description_id)
            ret.update(
                {
                    "description_id": description.pk,
                    "description_obj": description,
                    "description_text": description.description,
                }
            )
        return ret
    except Party.DoesNotExist:
        raise ValidationError(
            f"'{value}' is not a current party " f"identifier"
        )


class PartyIdentifierInput(forms.CharField):
    def clean(self, value):
        return party_and_description_dict_from_string(value)


class PartyChoiceField(forms.ChoiceField):
    def clean(self, value):
        value = super().clean(value)
        return party_and_description_dict_from_string(value)


class PartySelectField(forms.MultiWidget):
    def __init__(self, choices, attrs=None):
        widgets = [
            SelectWithAttrs(
                choices=choices,
                attrs={"disabled": True, "class": "party_widget_select"},
            ),
            forms.TextInput(attrs={"class": "party_widget_input"}),
        ]
        super().__init__(widgets, attrs)

    def decompress(self, value):
        if value:
            return value
        else:
            return ["", ""]


class PartyIdentifierField(forms.MultiValueField):
    def compress(self, data_list):
        if data_list:
            return self.to_python([v for v in data_list if v][-1])
        return None

    def __init__(self, *args, **kwargs):
        choices = kwargs.pop("choices", Party.objects.default_party_choices())

        kwargs["require_all_fields"] = False
        kwargs["label"] = kwargs.get("label", "Party")

        fields = (
            PartyChoiceField(required=False, disabled=True),
            PartyIdentifierInput(required=False),
        )
        super().__init__(fields, *args, **kwargs)
        self.widget = PartySelectField(choices=choices)
        self.widget.widgets[0].choices = choices
        self.fields[0].choices = choices

    def to_python(self, value):
        if not value:
            return value
        return value


class PopulatePartiesMixin:
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.populate_parties()

    def populate_parties(self):
        register = None
        for field_name, field_class in self.fields.items():
            if not isinstance(field_class.widget, BallotInputWidget):
                continue
            if field_name in self.initial:
                ballot = field_class.to_python(self.initial[field_name])
                register = ballot.post.party_set.slug

        # Populate the choices
        for field_name, field_class in self.fields.items():
            if not isinstance(field_class, PartyIdentifierField):
                continue
            if field_name not in self.initial:
                continue

            initial_for_field = self.initial[field_name]

            if not isinstance(initial_for_field, (list, tuple)):
                continue

            if not len(initial_for_field) == 2:
                continue

            extra_party_id = initial_for_field[1]
            if not extra_party_id:
                continue

            # Set the initial value of the select
            self.initial[field_name][0] = extra_party_id

            choices = Party.objects.party_choices(
                extra_party_ids=[extra_party_id], include_description_ids=True
            )
            self.fields[field_name] = PartyIdentifierField(choices=choices)
            self.fields[field_name].fields[0].choices = choices
