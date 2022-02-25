import django_filters
from candidates.models.popolo_extra import Ballot
from django.forms.widgets import HiddenInput
from elections.models import Election

from moderation_queue.models import QueuedImage


def get_ballots(request):
    return Ballot.objects.current_or_future().order_by().distinct()


def get_elections(request):
    return Election.objects.current_or_future()


class QueuedImageFilter(django_filters.FilterSet):
    """
    Allows QueuedImage list to be filtered.
    TODO decide which filters are most useful
    """

    # hidden because the choice list is huge, but having it allows linking direct from a ballot
    ballot_paper_id = django_filters.CharFilter(
        field_name="person__memberships__ballot__ballot_paper_id",
        label="Ballot paper id",
        widget=HiddenInput,
    )

    election = django_filters.ModelChoiceFilter(
        field_name="person__memberships__ballot__election",
        queryset=get_elections,
        label="Filter by current or future election",
    )

    class Meta:
        model = QueuedImage
        fields = ["ballot_paper_id", "election"]
