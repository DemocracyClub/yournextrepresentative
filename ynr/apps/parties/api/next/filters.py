from parties.models import Party
from api.next.filters import LastUpdatedFilter


class PartyFilter(LastUpdatedFilter):
    class Meta:
        model = Party
        fields = ["last_updated"]
