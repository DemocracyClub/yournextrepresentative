from django_filters import filterset, filters

from popolo.models import Membership
from uk_results.models import ResultSet


class ResultsFilterMixin(filterset.FilterSet):
    election_id = filters.CharFilter(
        field_name="ballot__election__slug",
        label="Election Slug",
        help_text="An election slug, used to get all "
        "results for a given election",
    )
    election_date = filters.DateFilter(
        field_name="ballot__election__election_date",
        label="Election Date",
        help_text="Election Date in ISO format",
    )
    last_updated = filters.DateTimeFilter(
        field_name="modified",
        lookup_expr="gt",
        label="Last updated",
        help_text="An ISO datetime",
    )


class ResultSetFilter(ResultsFilterMixin):
    class Meta:
        model = ResultSet
        fields = ["election_date", "election_id", "last_updated"]


class ElectedSetFilter(ResultsFilterMixin):
    class Meta:
        model = Membership
        fields = ["election_date", "election_id", "last_updated"]

    last_updated = filters.DateTimeFilter(
        field_name="modified",
        lookup_expr="gt",
        label="Last updated",
        help_text="An ISO datetime",
    )
