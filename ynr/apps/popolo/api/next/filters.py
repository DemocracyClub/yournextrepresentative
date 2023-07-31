from api.next.filters import LastUpdatedMixin
from popolo.models import Organization


class OrganizationFilter(LastUpdatedMixin):
    class Meta:
        model = Organization
        fields = ["last_updated"]
