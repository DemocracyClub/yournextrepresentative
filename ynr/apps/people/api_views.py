import json

from dateutil import parser
from django.db.models import Prefetch, Q
from django.http import Http404, HttpResponsePermanentRedirect
from rest_framework.decorators import action
from rest_framework import viewsets
from rest_framework.reverse import reverse
from rest_framework.response import Response

import people.serializers
from api.next.views import ResultsSetPagination
from candidates import models as extra_models
from candidates.serializers import LoggedActionSerializer
from people.models import Person
from popolo.models import Membership


class PersonViewSet(viewsets.ModelViewSet):
    def get_queryset(self):
        queryset = Person.objects.prefetch_related(
            Prefetch(
                "memberships",
                Membership.objects.select_related("party", "post"),
            ),
            "memberships__ballot__election",
            "tmp_person_identifiers",
            "other_names",
            "images",
        ).order_by("id")
        date_qs = self.request.query_params.get("updated_gte", None)
        if date_qs:
            date = parser.parse(date_qs)
            queryset = queryset.filter(
                Q(updated_at__gte=date) | Q(memberships__updated_at__gte=date)
            )
        return queryset

    def retrieve(self, request, *args, **kwargs):
        try:
            return super().retrieve(request, *args, **kwargs)
        except Http404 as e:
            try:
                lookup_url_kwarg = self.lookup_url_kwarg or self.lookup_field
                instance = extra_models.PersonRedirect.objects.get(
                    old_person_id=self.kwargs[lookup_url_kwarg]
                )
                return HttpResponsePermanentRedirect(
                    reverse(
                        "person-detail",
                        kwargs={
                            "pk": instance.new_person_id,
                            "version": kwargs["version"],
                        },
                    )
                )
            except extra_models.PersonRedirect.DoesNotExist:
                raise Http404(e)

    @action(detail=True, methods=["get"], name="Person History")
    def history(self, request, pk=None, **kwargs):
        qs = (
            extra_models.LoggedAction.objects.filter(person_id=pk)
            .select_related("person", "user")
            .order_by("-created")
        )

        page = self.paginate_queryset(qs)
        if page is not None:
            serializer = LoggedActionSerializer(
                page, many=True, context={"request": request}
            )
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(qs, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=["get"], name="Versions")
    def versions(self, request, pk=None, **kwargs):
        return Response(json.loads(self.get_object().versions))

    serializer_class = people.serializers.PersonSerializer
    pagination_class = ResultsSetPagination


class PersonRedirectViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = extra_models.PersonRedirect.objects.order_by("id")
    lookup_field = "old_person_id"
    serializer_class = people.serializers.PersonRedirectSerializer
    pagination_class = ResultsSetPagination
