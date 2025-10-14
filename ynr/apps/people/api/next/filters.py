import django_filters
from api.next.filters import LastUpdatedMixin
from candidates.models import PersonRedirect
from django_filters import filters, filterset
from people.models import Person


class PersonFilter(LastUpdatedMixin):
    class Meta:
        model = Person
        fields = ["last_updated"]

    has_identifier = django_filters.CharFilter(
        field_name="tmp_person_identifiers__value_type",
        help_text="Filter by the existence of an identifier type",
    )


class PersonRedirectFilter(filterset.FilterSet):
    class Meta:
        model = PersonRedirect
        fields = ["created"]

    created = filters.IsoDateTimeFilter(
        field_name="created",
        lookup_expr="gt",
        label="Last updated",
        help_text="An ISO datetime",
        method="filter_created",
    )

    def filter_created(self, queryset, name, value):
        return queryset.filter(created__gt=value)
