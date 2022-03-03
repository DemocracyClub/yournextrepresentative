import django_filters
from django.db.models import Max, Case, Value, When, IntegerField
from django.forms.widgets import HiddenInput
from django.utils.http import urlencode
from elections.filters import DSLinkWidget

from elections.models import Election
from moderation_queue.models import QueuedImage


def get_election_dates():
    """
    Returns election dates to filter the moderation queue by. To keep the
    number of choices down this is limited to elections that have a candidate
    with a QueuedImage awaiting review.
    """
    ballots_with_queued_images = (
        QueuedImage.objects.filter(decision=QueuedImage.UNDECIDED)
        .values("person__memberships__ballot")
        .distinct()
    )
    return (
        Election.objects.filter(ballot__in=ballots_with_queued_images)
        .values_list("election_date", "election_date")
        .distinct()
        .order_by("-election_date")
    )


def string_to_boolean(value):
    return {"True": True, "False": False}.get(value)


def bot_or_human(value):
    """
    Convert the string value into a boolean for the database query
    """
    return {"bot": True, "human": False}.get(value)


class QueuedImageFilter(django_filters.FilterSet):
    """
    Allows QueuedImage list to be filtered.
    """

    BOOLEAN_CHOICES = [(None, "---------"), ("True", "Yes"), ("False", "No")]

    # hidden because the choice list is huge, but having it allows linking direct from a ballot
    ballot_paper_id = django_filters.CharFilter(
        field_name="person__memberships__ballot__ballot_paper_id",
        label="Ballot paper id",
        widget=HiddenInput,
    )

    election_date = django_filters.TypedChoiceFilter(
        field_name="person__memberships__ballot__election__election_date",
        choices=get_election_dates,
        label="Election date",
        widget=DSLinkWidget,
    )

    election_slug = django_filters.CharFilter(
        field_name="person__memberships__ballot__election__slug",
        widget=HiddenInput,
    )

    current_election = django_filters.TypedChoiceFilter(
        field_name="person__memberships__ballot__election__current",
        choices=BOOLEAN_CHOICES,
        coerce=string_to_boolean,
        label="Candidates in a 'current' election",
        widget=DSLinkWidget,
    )

    no_photo = django_filters.TypedChoiceFilter(
        field_name="person__image",
        lookup_expr="isnull",
        choices=BOOLEAN_CHOICES,
        coerce=string_to_boolean,
        label="Has no current photo",
        widget=DSLinkWidget,
    )

    uploaded_by = django_filters.TypedChoiceFilter(
        field_name="user",
        lookup_expr="isnull",
        choices=[(None, "---------"), ("bot", "Robot 🤖"), ("human", "Human")],
        coerce=bot_or_human,
        label="Uploaded by a",
        widget=DSLinkWidget,
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
        widget=HiddenInput,
    )

    class Meta:
        model = QueuedImage
        fields = ["ballot_paper_id", "election_date"]

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

    @property
    def shortcuts(self):
        """
        Returns filter shorcuts
        """
        shortcut_list = [
            {
                "name": "no_photo",
                "label": "No current photo",
                "query": {"no_photo": ["True"]},
            },
            {
                "name": "current_election",
                "label": "In a current election",
                "query": {"current_election": ["True"]},
            },
            {
                "name": "uploaded_by",
                "label": "Uploaded by a robot 🤖",
                "query": {"uploaded_by": ["bot"]},
            },
        ]

        query = dict(self.request.GET)
        shortcuts = {"list": shortcut_list}
        for shortcut in shortcuts["list"]:
            shortcut["querystring"] = urlencode(shortcut["query"], doseq=True)
            if shortcut["query"] == query:
                shortcut["active"] = True
                shortcuts["active"] = shortcut
        return shortcuts
