import django_filters
from api.next.filters import LastUpdatedMixin
from candidates.models import PersonRedirect
from people.models import Person


class PersonFilter(LastUpdatedMixin):
    class Meta:
        model = Person
        fields = ["last_updated"]

    has_identifier = django_filters.CharFilter(
        field_name="tmp_person_identifiers__value_type",
        help_text="Filter by the existence of an identifier type",
    )


class PersonRedirectFilter(LastUpdatedMixin):
    class Meta:
        model = PersonRedirect
        fields = ["last_updated"]
