from rest_framework import viewsets
from rest_framework import filters as rf_filters
from django_filters import filters, filterset

from candidates.views import ResultsSetPagination

from ..models import CandidateResult, ResultSet
from ..serializers import CandidateResultSerializer, ResultSetSerializer


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



class ProductFilter(filterset.FilterSet):
    election_id = filters.CharFilter(
        name="post_election__election__slug")
    election_date = filters.DateFilter(
        name="post_election__election__election_date")

    class Meta:
        model = ResultSet
        fields = ['election_date', 'election_id']


class ResultSetViewSet(viewsets.ModelViewSet):
    queryset = ResultSet.objects \
        .select_related(
            'post_election__postextra__base',
            'user',
        ).order_by('id')
    serializer_class = ResultSetSerializer
    pagination_class = ResultsSetPagination

    filter_backends = (rf_filters.DjangoFilterBackend,)
    filter_class = ProductFilter
