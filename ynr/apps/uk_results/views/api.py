from django.db.models import Prefetch
from django_filters import filters, filterset
from rest_framework import viewsets

from api.v09.views import ResultsSetPagination
from uk_results.models import CandidateResult, ResultSet
from uk_results.serializers import (
    CandidateResultSerializer,
    ResultSetSerializer,
)


class CandidateResultViewSet(viewsets.ModelViewSet):
    queryset = CandidateResult.objects.select_related(
        "membership__party", "membership__post", "membership__person"
    ).order_by("id")
    serializer_class = CandidateResultSerializer
    pagination_class = ResultsSetPagination


class ResultSetFilter(filterset.FilterSet):
    election_id = filters.CharFilter(field_name="ballot__election__slug")
    election_date = filters.DateFilter(
        field_name="ballot__election__election_date"
    )

    class Meta:
        model = ResultSet
        fields = ["election_date", "election_id"]


class ResultSetViewSet(viewsets.ModelViewSet):
    queryset = ResultSet.objects.prefetch_related(
        "ballot__post",
        "ballot__election",
        "user",
        Prefetch(
            "candidate_results",
            CandidateResult.objects.select_related(
                "membership__party",
                "membership__post",
                "membership__person",
                "membership__ballot",
                "membership__ballot__post",
                "membership__ballot__election",
            ),
        ),
    ).order_by("id")

    serializer_class = ResultSetSerializer
    pagination_class = ResultsSetPagination

    filterset_class = ResultSetFilter
