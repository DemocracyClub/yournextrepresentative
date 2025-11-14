from urllib.parse import urlencode

import django_filters
from api.next.filters import LastUpdatedMixin
from candidates.models import Ballot
from django import forms
from django.db.models import BLANK_CHOICE_DASH
from django.utils.encoding import force_str
from django.utils.safestring import mark_safe
from django_filters.widgets import LinkWidget
from elections.models import Election
from uk_election_ids.datapackage import VOTING_SYSTEMS


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


def region_choices():
    """
    Return a list of tuples with NUTS1 code and label. Used by the region filter
    on the BaseBallotFilter
    """
    return [
        ("UKC", "North East"),
        ("UKD", "North West"),
        ("UKE", "Yorkshire and the Humber"),
        ("UKF", "East Midlands"),
        ("UKG", "West Midlands"),
        ("UKH", "East of England"),
        ("UKI", "London"),
        ("UKJ", "South East"),
        ("UKK", "South West"),
        ("UKL", "Wales"),
        ("UKM", "Scotland"),
        ("UKN", "Northern Ireland"),
    ]


class AnyBooleanWidget(forms.Select):
    """
    Same as BooleanWidget, but the default option is "any" rather than "unknown"
    """

    def __init__(self, attrs=None):
        choices = (("", "Any"), ("true", "Yes"), ("false", "No"))
        super().__init__(attrs, choices)


class FutureDateFilter(django_filters.BooleanFilter):
    def filter(self, qs, value):
        if value:
            qs = qs.future()
        return qs


class HasResultsFilter(django_filters.ChoiceFilter):
    def filter(self, qs, value):
        if not value:
            return qs
        if value in [True, "1"]:
            return qs.exclude(resultset=None)
        if value in [False, "0"]:
            return qs.filter(resultset=None)
        return qs


class DSLinkWidget(LinkWidget):
    """
    The LinkWidget doesn't allow iterating over choices in the template layer
    to change the HTML wrappig the widget.

    This breaks the way that Django *should* work, so we have to subclass
    and alter the HTML in Python :/

    https://github.com/carltongibson/django-filter/issues/880
    """

    def render(self, name, value, attrs=None, choices=(), renderer=None):
        if not hasattr(self, "data"):
            self.data = {}
        if value is None:
            value = ""
        self.build_attrs(self.attrs, extra_attrs=attrs)
        output = []
        options = self.render_options(choices, [value], name)
        if options:
            output.append(options)
        # output.append('</ul>')
        return mark_safe("\n".join(output))

    def render_option(self, name, selected_choices, option_value, option_label):
        option_value = force_str(option_value)
        if option_label == BLANK_CHOICE_DASH[0][1]:
            option_label = "All"
        data = self.data.copy()
        data[name] = option_value
        selected = data == self.data or option_value in selected_choices
        # remove page param from query string
        if data.get("page"):
            del data["page"]
        try:
            url = data.urlencode()
        except AttributeError:
            url = urlencode(data)
        return self.option_string() % {
            "attrs": selected and ' aria-current="true"' or "",
            "query_string": url,
            "label": force_str(option_label),
        }


class BaseBallotFilter(django_filters.FilterSet):
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
            return queryset.exclude(sopn=None)
        return queryset.filter(sopn=None)

    def is_by_election_filter(self, queryset, name, value):
        if int(value):
            return queryset.filter(ballot_paper_id__contains=".by.")
        return queryset.exclude(ballot_paper_id__contains=".by.")

    def is_cancelled_filter(self, queryset, name, value):
        if int(value):
            return queryset.filter(cancelled=True)
        return queryset.filter(cancelled=False)

    def election_type_filter(self, queryset, name, value):
        return queryset.filter(election__slug__startswith=value)

    def region_filter(self, queryset, name, value):
        """
        Filter queryset by region using the NUTS1 code
        """
        return queryset.by_region(code=value)

    def postcode_filter(self, queryset, name, value):
        """
        Filter queryset by postcode
        """
        return queryset.for_postcode(postcode=value)

    review_required = django_filters.ChoiceFilter(
        field_name="review_required",
        method="lock_status",
        widget=DSLinkWidget(),
        label="Lock status",
        help_text="One of `locked`, `suggestion` or `unlocked`.",
        choices=[
            ("locked", "Locked"),
            ("suggestion", "Lock suggestion"),
            ("unlocked", "Unlocked"),
        ],
    )

    has_sopn = django_filters.ChoiceFilter(
        field_name="has_sopn",
        method="has_sopn_filter",
        widget=DSLinkWidget(),
        label="Has SoPN",
        help_text="""Boolean, `1` for ballots that have a
            SOPN uploaded or `0` for ballots without SOPNs""",
        choices=[(1, "Yes"), (0, "No")],
    )

    election_type = django_filters.ChoiceFilter(
        widget=DSLinkWidget(),
        method="election_type_filter",
        choices=election_types_choices,
        label="Election Type",
        help_text="A valid [election type](https://elections.democracyclub.org.uk/election_types/)",
    )

    filter_by_region = django_filters.ChoiceFilter(
        widget=DSLinkWidget(),
        method="region_filter",
        label="Filter by region",
        choices=region_choices,
    )

    is_by_election = django_filters.ChoiceFilter(
        field_name="is_by_election",
        method="is_by_election_filter",
        widget=DSLinkWidget(),
        label="By election",
        help_text="""Boolean, `1` for by-elections `0` for scheduled
        elections""",
        choices=[(1, "Yes"), (0, "No")],
    )

    is_cancelled = django_filters.ChoiceFilter(
        field_name="is_cancelled",
        method="is_cancelled_filter",
        widget=DSLinkWidget(),
        label="Cancelled",
        help_text="""Boolean, `1` for cancelled `0` taking place""",
        choices=[(1, "Yes"), (0, "No")],
    )

    for_postcode = django_filters.CharFilter(
        label="For postcode",
        help_text="""Find ballots covering a postcode.""",
        method="postcode_filter",
    )

    class Meta:
        model = Ballot
        fields = ["review_required", "has_sopn"]


class BallotFilter(BaseBallotFilter, LastUpdatedMixin):
    """
    Used on the API

    """

    election_date = django_filters.DateFilter(
        field_name="election__election_date",
        label="Election Date in ISO format",
        help_text="Election Date in ISO format",
    )

    election_date_range = django_filters.DateFromToRangeFilter(
        field_name="election__election_date",
        label="Election Date Range",
        help_text="""Use `election_date_range_before` and
        `election_date_range_after` with ISO dates to get ballots
        inside this range.
        """,
    )

    election_id = django_filters.CharFilter(
        field_name="election__slug",
        help_text="""An election
        [slug](/api/docs/next/definitions/#Election/slug), used to get all
        ballots for a given election""",
    )

    future = FutureDateFilter(
        label="Election in Future",
        widget=AnyBooleanWidget,
        help_text="Boolean. Election dates in the future.",
    )
    current = django_filters.BooleanFilter(
        field_name="election__current",
        label="Election Current",
        widget=AnyBooleanWidget,
        help_text="""Boolean. Elections are typically marked as `current` when
        the election date is 90 days in the future and 20 days in the past.

This may change depending on the elections. Used to determine if
        Democracy Club considers this election to be of current interest, e.g.
        for showing results after polling day.
        """,
    )

    has_results = HasResultsFilter(
        label="Has Results",
        widget=AnyBooleanWidget,
        help_text="""Boolean. If results have been entered for this ballot.
        Only First Past The Post ballots have results at the moment.""",
    )

    voting_system = django_filters.ChoiceFilter(
        field_name="voting_system",
        choices=[(key, value["name"]) for key, value in VOTING_SYSTEMS.items()],
        help_text=f"""One of {", ".join([f"`{key}`" for key in VOTING_SYSTEMS])}""",
    )

    def filter_last_updated(self, queryset, name, value):
        """
        Method for the last_updated filter. Uses the last_updated QuerysetMethod
        to return updated after the given datetime
        """
        return queryset.last_updated(datetime=value)


class CurrentOrFutureBallotFilter(BaseBallotFilter):
    """
    Same as Ballot Filter, but only present options related to current
    elections
    """

    def has_result_set_filter(self, queryset, name, value):
        """
        Filter queryset by if they have a result set or not
        """
        mapping = {
            1: "complete_result_set",
            0: "no_result_set",
            2: "incomplete_result_set",
        }
        has_result_set_or_not = getattr(queryset, mapping[int(value)])
        return has_result_set_or_not()

    election_type = django_filters.ChoiceFilter(
        widget=DSLinkWidget(),
        method="election_type_filter",
        choices=current_election_types_choices,
        label="Election Type",
    )

    has_results = HasResultsFilter(
        label="Has Candidate Results",
        # method="has_results_filter",
        widget=DSLinkWidget(),
        choices=[(1, "Yes"), (0, "No")],
    )

    has_result_set = django_filters.ChoiceFilter(
        label="Has Result Set",
        method="has_result_set_filter",
        widget=DSLinkWidget(),
        choices=[(1, "Yes"), (0, "No"), (2, "Incomplete")],
    )


def filter_shortcuts(request):
    shortcut_list = [
        {
            "name": "data_input",
            "label": "Ready for data input",
            "query": {
                "review_required": ["unlocked"],
                "has_sopn": ["1"],
                "is_cancelled": ["0"],
            },
        },
        {
            "name": "has_results",
            "label": "Ready for results",
            "query": {
                "has_results": ["0"],
                "review_required": ["locked"],
                "is_cancelled": ["0"],
            },
        },
    ]

    query = dict(request.GET)
    shortcuts = {"list": shortcut_list}
    for shortcut in shortcuts["list"]:
        shortcut["querystring"] = urlencode(shortcut["query"], doseq=True)
        if shortcut["query"] == query:
            shortcut["active"] = True
            shortcuts["active"] = shortcut
    return shortcuts
