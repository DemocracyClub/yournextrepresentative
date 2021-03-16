import json

from django.http import HttpResponse
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
from django.views import View
from rest_framework import viewsets

from api.helpers import DefaultPageNumberPagination

from parties.models import Party
from parties.api.next.serializers import (
    PartySerializer,
    PartyRegisterSerializer,
)


class PartyViewSet(viewsets.ReadOnlyModelViewSet):
    """


    """

    queryset = Party.objects.all().prefetch_related("emblems", "descriptions")
    serializer_class = PartySerializer
    lookup_field = "ec_id"
    pagination_class = DefaultPageNumberPagination

    def retrieve(self, request, *args, **kwargs):
        """
        A single `Party` object
        """
        return super().retrieve(request, *args, **kwargs)


class PartyRegisterList(viewsets.ReadOnlyModelViewSet):
    """
    Return a list of all party register values, used for
    discovery of filter values in the `parties` endpoint.
    """

    serializer_class = PartyRegisterSerializer
    pagination_class = DefaultPageNumberPagination
    queryset = Party.objects.order_by("register").distinct("register")

    def retrieve(self, request, *args, **kwargs):
        """
        A single `PartyRegister` object
        """
        return super().retrieve(request, *args, **kwargs)

    @method_decorator(cache_page(60 * 60 * 24))
    def list(self, request, version, format=None):
        qs = self.get_queryset()

        page = self.paginate_queryset(qs)
        if page is not None:
            serializer = PartyRegisterSerializer(qs, many=True)
            return self.get_paginated_response(serializer.data)


class AllPartiesJSONView(View):

    http_method_names = ["get"]

    def get(self, request, *args, **kwargs):
        register = self.request.GET.get("register", None)
        status_code = 200
        ps = Party.objects.current()
        if register:
            ps = ps.register(register)
        ret = {"items": []}
        qs = ps.party_choices(
            exclude_deregistered=True, include_description_ids=True
        )

        for party in qs:
            item = {}

            if type(party[1]) == list:
                # This is a party with descriptions
                item["text"] = party[0]
                item["children"] = []
                for child in party[1]:
                    item["children"].append(
                        {
                            "id": child[0],
                            "text": child[1]["label"],
                            "register": child[1]["register"],
                        }
                    )
            else:
                # This party doesn't have descriptions
                item = {
                    "id": party[0],
                    "text": party[1]["label"],
                    "register": party[1].get("register", "all"),
                }

            ret["items"].append(item)

        return HttpResponse(
            json.dumps(ret), content_type="application/json", status=status_code
        )
