from popolo.models import Organization
from api.next.filters import LastUpdatedMixin


class OrganizationFilter(LastUpdatedMixin):
    class Meta:
        model = Organization
        fields = ["last_updated"]
