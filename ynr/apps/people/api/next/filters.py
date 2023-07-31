import django_filters
from api.next.filters import LastUpdatedMixin
from people.models import Person


class PersonFilter(LastUpdatedMixin):
    class Meta:
        model = Person
        fields = ["last_updated"]

    has_identifier = django_filters.CharFilter(
        field_name="tmp_person_identifiers__value_type",
        help_text="Filter by the existence of an identifier type",
    )
