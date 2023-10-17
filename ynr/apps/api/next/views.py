from datetime import date, datetime

import api.next.serializers
import candidates.api.next.serializers
from candidates import models as extra_models
from candidates.filters import LoggedActionAPIFilter
from popolo.api.next.filters import OrganizationFilter
from popolo.models import Organization
from rest_framework import pagination, viewsets


def parse_date(date_text):
    if date_text == "today":
        return date.today()
    try:
        return datetime.strptime(date_text, "%Y-%m-%d").date()
    except ValueError:
        return None


# Now the django-rest-framework based API views:
class ResultsSetPagination(pagination.PageNumberPagination):
    page_size = 10
    page_size_query_param = "page_size"
    max_page_size = 100


class OrganizationViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = (
        Organization.objects.all()
        .order_by("slug")
        .exclude(classification="Party")
    )
    lookup_field = "slug"
    serializer_class = api.next.serializers.OrganizationSerializer
    pagination_class = ResultsSetPagination
    filterset_class = OrganizationFilter


class LoggedActionViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = extra_models.LoggedAction.objects.order_by("id")
    serializer_class = candidates.api.next.serializers.LoggedActionSerializer
    pagination_class = ResultsSetPagination

    filterset_class = LoggedActionAPIFilter
