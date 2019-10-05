import json

from django.http import HttpResponse
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
from django.views import View
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

    @method_decorator(cache_page(60 * 60 * 24))
    def list(self, request, version):
        registers = (
            Party.objects.order_by("register")
            .values_list("register", flat=True)
            .distinct("register")
        )
        return Response(registers)


class AllPartiesJSONView(View):

    http_method_names = ["get"]

    def get(self, request, *args, **kwargs):
        register = self.request.GET.get("register", "").upper()
        status_code = 200
        if not register or register not in ["GB", "NI"]:
            ret = {
                "error": "Please provide a `register` as a GET param that equals either `NI` or `GB`"
            }
            status_code = 400
        else:
            ps = Party.objects.register(register)
            ret = {"items": []}
            qs = ps.party_choices(
                exclude_deregistered=True, include_description_ids=True
            )

            for party in qs:
                item = {}
                if type(party[1]) == list:
                    item["text"] = party[0]
                    item["children"] = []
                    for child in party[1]:
                        item["children"].append(
                            {"id": child[0], "text": child[1]}
                        )
                else:
                    item["id"] = party[0]
                    item["text"] = party[1]

                ret["items"].append(item)

        return HttpResponse(
            json.dumps(ret), content_type="application/json", status=status_code
        )
