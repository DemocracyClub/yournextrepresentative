from urllib.parse import urlencode

import django_filters
from django_filters.widgets import LinkWidget

from candidates.models import Ballot
from elections.models import Election


def _get_election_types_choices_for_qs(qs):
    qs = (
        qs.order_by("for_post_role")
        .distinct("for_post_role")
        .values("slug", "for_post_role")
    )
    return [(e["slug"].split(".")[0], e["for_post_role"]) for e in qs]


def election_types_choices():
    qs = Election.objects.all()
    return _get_election_types_choices_for_qs(qs)


def current_election_types_choices():
    qs = Election.objects.current_or_future()
    return _get_election_types_choices_for_qs(qs)


class BallotFilter(django_filters.FilterSet):
    def lock_status(self, queryset, name, value):
        """
        Unlocked ballots with a document but no lock suggestion
        """
        kwargs = {}

        if value == "locked":
            kwargs["candidates_locked"] = True
        elif value == "suggestion":
            kwargs["suggestedpostlock__isnull"] = False
            kwargs["candidates_locked"] = False
        elif value == "unlocked":
            kwargs["suggestedpostlock__isnull"] = True
            kwargs["candidates_locked"] = False

        return queryset.filter(**kwargs)

    def has_sopn_filter(self, queryset, name, value):
        if int(value):
            return queryset.exclude(officialdocument=None)
        else:
            return queryset.filter(officialdocument=None)

    def election_type_filter(self, queryset, name, value):
        return queryset.filter(election__slug__startswith=value)

    review_required = django_filters.ChoiceFilter(
        field_name="review_required",
        method="lock_status",
        widget=LinkWidget(),
        label="Lock status",
        choices=[
            ("locked", "Locked"),
            ("suggestion", "Lock suggestion"),
            ("unlocked", "Unlocked"),
        ],
    )

    has_sopn = django_filters.ChoiceFilter(
        field_name="has_sopn",
        method="has_sopn_filter",
        widget=LinkWidget(),
        label="Has SoPN",
        choices=[(1, "Yes"), (0, "No")],
    )

    election_type = django_filters.ChoiceFilter(
        widget=LinkWidget(),
        method="election_type_filter",
        choices=election_types_choices,
        label="Election Type",
    )

    class Meta:
        model = Ballot
        fields = ["review_required", "has_sopn"]


class CurrentOrFutureBallotFilter(BallotFilter):
    """
    Same as Ballot Filter, but only present options related to current
    elections
    """

    election_type = django_filters.ChoiceFilter(
        widget=LinkWidget(),
        method="election_type_filter",
        choices=current_election_types_choices,
        label="Election Type",
    )


def filter_shortcuts(request):
    shortcut_list = [
        {
            "name": "data_input",
            "label": "Ready for data input",
            "query": {"review_required": ["unlocked"], "has_sopn": ["1"]},
        }
    ]

    query = dict(request.GET)
    shortcuts = {"list": shortcut_list}
    for shortcut in shortcuts["list"]:
        shortcut["querystring"] = urlencode(shortcut["query"], doseq=True)
        if shortcut["query"] == query:
            shortcut["active"] = True
            shortcuts["active"] = shortcut
    return shortcuts
