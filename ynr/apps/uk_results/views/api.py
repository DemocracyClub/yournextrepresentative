from rest_framework import serializers, viewsets, filters

from django.db.models import Prefetch

import django_filters
from django_filters.widgets import BooleanWidget

from candidates.serializers import OrganizationExtraSerializer
from candidates.views import ResultsSetPagination

from ..serializers import (
    CandidateResultSerializer, ResultSetSerializer
)
from ..models import (
    CandidateResult, ResultSet,
)


class CandidateResultViewSet(viewsets.ModelViewSet):
    queryset = CandidateResult.objects \
        .select_related(
            'membership__on_behalf_of__extra',
            'membership__organization__extra',
            'membership__post__extra',
            'membership__extra__election',
            'membership__person',
        ) \
        .order_by('id')
    serializer_class = CandidateResultSerializer
    pagination_class = ResultsSetPagination


class ResultSetViewSet(viewsets.ModelViewSet):
    queryset = ResultSet.objects \
        .select_related(
            'post_election_result__post_election__postextra',
            'user',
        ) \
        .order_by('id')
    serializer_class = ResultSetSerializer
    pagination_class = ResultsSetPagination

    filter_backends = (filters.DjangoFilterBackend,)
    filter_fields = ['review_status',]
