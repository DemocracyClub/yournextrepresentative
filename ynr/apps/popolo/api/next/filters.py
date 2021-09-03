from popolo.models import Organization
from api.next.filters import LastUpdatedFilter


class OrganizationFilter(LastUpdatedFilter):
    class Meta:
        model = Organization
        fields = ["last_updated"]
