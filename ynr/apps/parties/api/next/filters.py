from parties.models import Party
from api.next.filters import LastUpdatedMixin


class PartyFilter(LastUpdatedMixin):
    class Meta:
        model = Party
        fields = ["last_updated"]
