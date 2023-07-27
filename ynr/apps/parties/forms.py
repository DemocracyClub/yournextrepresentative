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

    def validate(self, value):
        """
        Because we don't always show all parties on the initial page load (we
        leave JavaScript to add the non-current parties sometimes), we need to
        ignore any input value for this field type. The MultiWidget will
        raise a ValidataionError if the party isn't actually found, so there's
        no problem with ignoring validation here.
        """
        try:
            Party.objects.current().get(ec_id__iexact=value.strip())
            return True
        except Party.DoesNotExist:
            return False


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
        return ["", ""]


class PreviousPartyAffiliationsField(forms.MultipleChoiceField):
    def __init__(self, required=False, choices=None, *args, **kwargs):
        self.membership = kwargs.pop("membership", None)
        choices = choices or self.get_previous_party_affiliations_choices()
        super().__init__(required=required, choices=choices, *args, **kwargs)

    def widget_attrs(self, widget):
        """
        Sets the class used to initialise select2
        """
        return {"class": "previous-party-affiliations"}

    def get_previous_party_affiliations_choices(self):
        """
        Return a party choices made up of parties that have been active any time
        within a year of the election date. Only applicable to welsh run ballots
        """
        if self.membership is None:
            return []

        ballot = self.membership.ballot
        if not ballot.is_welsh_run:
            return []

        parties = Party.objects.register("GB").active_in_last_year(
            date=ballot.election.election_date
        )
        return parties.values_list("ec_id", "name")


class PartyIdentifierField(forms.MultiValueField):
    def compress(self, data_list):
        if data_list:
            return self.to_python([v for v in data_list if v][-1])
        return None

    def __init__(self, *args, choices=None, **kwargs):
        if not choices:
            choices = [("", "")]
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
    _cached_choices = None

    def __init__(self, **kwargs):
        party_choices = kwargs.pop("party_choices", None)
        if party_choices:
            self._cached_choices = party_choices
        super().__init__(**kwargs)
        self.populate_parties()

    def populate_parties(self):
        register = None
        for field_name, field_class in self.fields.items():
            if not isinstance(field_class.widget, BallotInputWidget):
                continue
            if field_name in self.initial:
                ballot = field_class.to_python(self.initial[field_name])
                register = ballot.post.party_set.slug.upper()

        # Populate the choices
        for field_name, field_class in self.fields.items():
            if not isinstance(field_class, PartyIdentifierField):
                continue

            choices_kwargs = {"include_description_ids": True}
            if field_name in self.initial:
                initial_for_field = self.initial[field_name]
                if not isinstance(initial_for_field, (list, tuple)):
                    raise ValueError("list or tuple required for initial")

                if len(initial_for_field) != 2:
                    continue

                extra_party_id = initial_for_field[1]

                if extra_party_id:
                    choices_kwargs["extra_party_ids"] = ([extra_party_id],)

                # Set the initial value of the select
                self.initial[field_name][0] = extra_party_id

            if not self._cached_choices:
                base_qs = Party.objects.all().current()
                if register:
                    base_qs = base_qs.register(register)
                self._cached_choices = base_qs.party_choices(**choices_kwargs)
            choices = self._cached_choices
            self.fields[field_name] = PartyIdentifierField(choices=choices)
            self.fields[field_name].fields[0].choices = choices
