import django_filters
from candidates.models.popolo_extra import Ballot
from django.forms.widgets import HiddenInput
from elections.models import Election
from django.db.models import Max, Case, Value, When, IntegerField

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

    ordering = django_filters.OrderingFilter(
        choices=[
            ("-election_date", "Election date candidate is standing in"),
            (
                "election_date",
                "Election date candidate is standing in (oldest first)",
            ),
            ("-current_election", "Current election"),
            ("current_election", "Current election (not current first)"),
            ("-created", "Date uploaded (newest first)"),
            ("created", "Date uploaded (oldest first)"),
        ],
        fields=[
            ("election_date", "election_date"),
            ("current_election", "current_election"),
            ("created", "created"),
        ],
    )

    class Meta:
        model = QueuedImage
        fields = ["ballot_paper_id", "election"]

    def __init__(self, *args, **kwargs):
        """
        Annotates the querset to ensure that fields used for ordering are
        annotated.
        Aggregations are used to avoid duplicate objects being returned when
        ordering on related fields.
        """
        kwargs["queryset"] = kwargs["queryset"].annotate(
            election_date=Max(
                "person__memberships__ballot__election__election_date"
            ),
            current_election=Max(
                Case(
                    When(
                        person__memberships__ballot__election__current=True,
                        then=Value(1),
                    ),
                    default=0,
                    output_field=IntegerField(),
                )
            ),
        )
        super().__init__(*args, **kwargs)
