from api.next.filters import LastUpdatedMixin
from parties.models import Party


class PartyFilter(LastUpdatedMixin):
    class Meta:
        model = Party
        fields = ["last_updated"]
