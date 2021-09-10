from people.models import Person
from api.next.filters import LastUpdatedMixin


class PersonFilter(LastUpdatedMixin):
    class Meta:
        model = Person
        fields = ["last_updated"]
