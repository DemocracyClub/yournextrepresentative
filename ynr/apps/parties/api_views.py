from rest_framework import viewsets

from .models import Party
from .serializers import PartySerializer


class PartyViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Party.objects.all()
    serializer_class = PartySerializer
    lookup_field = "ec_id"
