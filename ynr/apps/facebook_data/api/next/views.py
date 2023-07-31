from api.next.views import ResultsSetPagination
from facebook_data.api.next.serializers import FacebookAdvertSerializer
from facebook_data.filters import FacebookAdvertFilterSet
from facebook_data.models import FacebookAdvert
from rest_framework import viewsets


class FacebookAdvertViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = FacebookAdvert.objects.all().select_related("person")

    serializer_class = FacebookAdvertSerializer
    pagination_class = ResultsSetPagination
    filterset_class = FacebookAdvertFilterSet
