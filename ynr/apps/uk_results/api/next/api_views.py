from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from api.helpers import DefaultPageNumberPagination
from popolo.api.next.serializers import CandidacyOnBallotSerializer
from popolo.models import Membership
from uk_results.api.next.filters import ResultSetFilter, ElectedSetFilter
from uk_results.models import ResultSet

from uk_results.api.next.serializers import ResultSerializer, ElectedSerializer


class ResultViewSet(viewsets.ReadOnlyModelViewSet):
    lookup_field = "ballot__ballot_paper_id"
    lookup_value_regex = r"(?!\.json$)[^/]+"
    lookup_url_kwarg = "ballot_paper_id"
    queryset = (
        ResultSet.objects.select_related("ballot")
        .prefetch_related("ballot__membership_set")
        .order_by("-ballot__election__election_date", "ballot__ballot_paper_id")
    )
    serializer_class = ResultSerializer
    pagination_class = DefaultPageNumberPagination
    filterset_class = ResultSetFilter

    @action(detail=True, methods=["get"], name="Previous versions")
    def versions(self, request, ballot_paper_id=None, **kwargs):
        """
        A log of the previous versions of results entered. This
        is due to mistakes in entering the data, or sometimes mistakes in the
        published data that get corrected at a later date.
        """
        rs = ResultSet.objects.get(ballot__ballot_paper_id=ballot_paper_id)
        return Response(rs.versions)


class ElectedViewSet(viewsets.ReadOnlyModelViewSet):
    """
    A list of candidates that have been marked as Elected.

    Elected candidates might not have votes cast results recorded against
    them yet.
    """

    queryset = Membership.objects.select_related(
        "ballot", "person", "party"
    ).filter(elected=True)

    serializer_class = ElectedSerializer
    filterset_class = ElectedSetFilter
