from rest_framework import viewsets
from rest_framework.response import Response

from api.helpers import ResultsSetPagination

from .models import Party
from .serializers import PartySerializer


class PartyViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Party.objects.all().prefetch_related("emblems", "descriptions")
    serializer_class = PartySerializer
    lookup_field = "ec_id"
    pagination_class = ResultsSetPagination


class PartyRegisterList(viewsets.ViewSet):
    """
    Return a list of all party register values, used for
    discovery of filter values in the `parties` endpoint.
    """

    def list(self, request, version):
        registers = (
            Party.objects.order_by("register")
            .values_list("register", flat=True)
            .distinct("register")
        )
        return Response(registers)
