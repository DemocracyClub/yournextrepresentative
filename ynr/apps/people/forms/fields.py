from django import forms
from django.contrib.auth.models import AnonymousUser
from django.core.exceptions import ValidationError
from django_date_extensions.fields import ApproximateDateFormField

from candidates.models import Ballot


class BallotInputWidget(forms.TextInput):
    def __init__(self, attrs=None):
        super().__init__(attrs)
        existing_class = self.attrs.get("class", "")
        self.attrs["class"] = " ".join(
            existing_class.split(" ") + ["js-ballot-input"]
        ).strip()


class ValidBallotField(forms.CharField):
    def __init__(self, *args, **kwargs):
        user = kwargs.pop("user", None)
        if user:
            self.user = user
        else:
            self.user = AnonymousUser
        super().__init__(*args, **kwargs)

    widget = BallotInputWidget

    def to_python(self, value):
        if not value:
            return value
        return Ballot.objects.get(ballot_paper_id=value)

    def clean(self, value):
        if not value:
            return value
        value = value.lower()
        if len(value.split(".")) < 3:
            raise ValidationError("Invalid ballot paper ID")
        base_qs = Ballot.objects.all().select_related("election")
        try:
            ballot = base_qs.get(ballot_paper_id__iexact=value.strip())
            return ballot
        except Ballot.DoesNotExist:
            raise ValidationError("Unknown ballot paper ID")


class CurrentUnlockedBallotsField(ValidBallotField):
    def clean(self, value):
        ballot = super().clean(value)

        if ballot.candidates_locked:
            raise ValidationError("Cannot add candidates to a locked " "ballot")
        if not ballot.election.current:
            raise ValidationError(
                "Cannot update an election that isn't 'current'"
            )
        if ballot.cancelled and not self.user.is_staff:
            raise ValidationError(
                "Cannot add candidates to a cancelled election"
            )
        return ballot


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
