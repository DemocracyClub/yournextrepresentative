from dateutil import parser
from django.db.models import Prefetch, Q
from rest_framework import viewsets

import people.serializers
from api.next.views import ResultsSetPagination
from candidates import models as extra_models
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

    serializer_class = people.serializers.PersonSerializer
    pagination_class = ResultsSetPagination


class PersonRedirectViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = extra_models.PersonRedirect.objects.order_by("id")
    lookup_field = "old_person_id"
    serializer_class = people.serializers.PersonRedirectSerializer
    pagination_class = ResultsSetPagination
