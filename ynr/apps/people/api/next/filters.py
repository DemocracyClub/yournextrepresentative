from people.models import Person
from api.next.filters import LastUpdatedFilter


class PersonFilter(LastUpdatedFilter):
    class Meta:
        model = Person
        fields = ["last_updated"]
