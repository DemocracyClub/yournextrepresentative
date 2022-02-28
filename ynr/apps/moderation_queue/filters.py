import django_filters
from django.db.models import Max, Case, Value, When, IntegerField
from django.forms.widgets import HiddenInput

from elections.models import Election
from moderation_queue.models import QueuedImage


def get_elections(request):
    """
    Returns election objects to filter the moderation queue by. To keep the
    number of choices down this is limited to elections that have a candidate
    with a QueuedImage awaiting review.
    """
    ballots_with_queued_images = (
        QueuedImage.objects.filter(decision=QueuedImage.UNDECIDED)
        .values_list("person__memberships__ballot", flat=True)
        .distinct()
    )
    return Election.objects.filter(
        ballot__in=ballots_with_queued_images
    ).distinct()


def string_to_boolean(value):
    return {"True": True, "False": False}.get(value)


class QueuedImageFilter(django_filters.FilterSet):
    """
    Allows QueuedImage list to be filtered.
    TODO decide which filters are most useful
    """

    BOOLEAN_CHOICES = [
        (None, "---------"),
        ("True", "True"),
        ("False", "False"),
    ]

    # hidden because the choice list is huge, but having it allows linking direct from a ballot
    ballot_paper_id = django_filters.CharFilter(
        field_name="person__memberships__ballot__ballot_paper_id",
        label="Ballot paper id",
        widget=HiddenInput,
    )

    election = django_filters.ModelChoiceFilter(
        field_name="person__memberships__ballot__election",
        queryset=get_elections,
        label="Filter by election - only elections that have a candidate with a queued image are included",
    )

    current_election = django_filters.TypedChoiceFilter(
        field_name="person__memberships__ballot__election__current",
        choices=BOOLEAN_CHOICES,
        coerce=string_to_boolean,
        label="Candidates in a 'current' election",
    )

    has_photo = django_filters.TypedChoiceFilter(
        field_name="person__image",
        lookup_expr="isnull",
        choices=BOOLEAN_CHOICES,
        coerce=string_to_boolean,
        label="Has no current photo",
    )

    uploaded_by = django_filters.TypedChoiceFilter(
        field_name="user",
        lookup_expr="isnull",
        choices=[(None, "---------"), ("True", "Script"), ("False", "Human")],
        coerce=string_to_boolean,
        label="Uploaded by a",
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
