from django import forms
from django.core.exceptions import ValidationError
from django_date_extensions.fields import ApproximateDateFormField

from candidates.models import Ballot
from parties.models import Party


class CurrentUnlockedBallotsField(forms.CharField):
    def clean(self, value):
        if not value:
            return value
        value = value.lower()
        if len(value.split(".")) < 3:
            raise ValidationError("Invalid ballot paper ID")
        base_qs = Ballot.objects.all().select_related("election")
        try:
            ballot = base_qs.get(ballot_paper_id__iexact=value.strip())
            if ballot.candidates_locked:
                raise ValidationError(
                    "Cannot add candidates to a locked " "ballot"
                )
            if not ballot.election.current:
                raise ValidationError(
                    "Cannot update an election that isn't 'current'"
                )
            if ballot.cancelled:
                raise ValidationError(
                    "Cannot add candidates to a cancelled election"
                )
            return ballot
        except Ballot.DoesNotExist:
            raise ValidationError("Unknown ballot paper ID")

    def to_python(self, value):
        if not value:
            return value
        return Ballot.objects.get(ballot_paper_id=value)


class PartyIdentiferField(forms.CharField):
    party = None

    def clean(self, value):
        if not value:
            return value
        value = value.strip()
        base_qs = Party.objects.all()
        try:
            if not self.party:
                self.party = base_qs.get(ec_id=value)
            return self.party
        except Party.DoesNotExist:
            raise ValidationError(f"No party with ID {value} exists")

    def to_python(self, value):
        if not value:
            return value
        if not self.party:
            self.party = Party.objects.get(ec_id=value)
        return self.party


class StrippedCharField(forms.CharField):
    """A backport of the Django 1.9 ``CharField`` ``strip`` option.

    If ``strip`` is ``True`` (the default), leading and trailing
    whitespace is removed.
    """

    def __init__(
        self, max_length=None, min_length=None, strip=True, *args, **kwargs
    ):
        self.strip = strip
        super().__init__(
            max_length=max_length, min_length=min_length, *args, **kwargs
        )

    def to_python(self, value):
        value = super().to_python(value)
        if self.strip:
            value = value.strip()
        return value


class BlankApproximateDateFormField(ApproximateDateFormField):
    """
    The same as ApproximateDateFormField but returns an empty string rather
    than None for blank values and a date string for valid dates.
    """

    def clean(self, value):
        if type(value) == str:
            value = value.replace("-00", "-01")
        value = super().clean(value)
        if not value:
            return ""
        return "{year:04d}-{month:02d}-{day:02d}".format(
            year=value.year, month=value.month, day=value.day
        )
