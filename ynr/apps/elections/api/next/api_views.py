from typing import OrderedDict
from django.db.models import Prefetch
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

import elections.api.next.serializers
from api.next.views import ResultsSetPagination
from candidates import models as extra_models
from candidates.api.next.serializers import LoggedActionSerializer
from elections.filters import BallotFilter
from elections.models import Election
from official_documents.models import OfficialDocument
from popolo.models import Membership
from utils.db import LastWord


class ElectionViewSet(viewsets.ReadOnlyModelViewSet):
    lookup_value_regex = r"(?!\.json$)[^/]+"
    queryset = Election.objects.order_by("id")
    lookup_field = "slug"
    serializer_class = elections.api.next.serializers.ElectionSerializer
    filterset_fields = ("current",)
    pagination_class = ResultsSetPagination


class BallotViewSet(viewsets.ReadOnlyModelViewSet):
    """
    A paginated list of all ballots

    """

    lookup_field = "ballot_paper_id"
    lookup_value_regex = r"(?!\.json$)[^/]+"
    queryset = (
        extra_models.Ballot.objects.select_related(
            "election", "post", "replaces", "replaced_by"
        )
        .prefetch_related(
            Prefetch(
                "membership_set",
                queryset=Membership.objects.all()
                .select_related("result", "person", "party")
                .annotate(last_name=LastWord("person__name"))
                .order_by(
                    "-elected",
                    "-result__num_ballots",
                    "party_list_position",
                    "person__sort_name",
                    "last_name",
                ),
            ),
            Prefetch(
                "officialdocument_set",
                queryset=OfficialDocument.objects.filter(
                    document_type=OfficialDocument.NOMINATION_PAPER
                ).order_by("modified"),
            ),
        )
        .order_by("-election__election_date", "ballot_paper_id")
    )
    serializer_class = elections.api.next.serializers.BallotSerializer
    pagination_class = ResultsSetPagination

    filterset_class = BallotFilter

    def list(self, request, *args, **kwargs):
        """
        If the last_updated filter param is used objects are ordered oldest
        changes first, and in maximum chunks of 200
        """
        is_last_updated_query = self.request.query_params.get("last_updated")
        if not is_last_updated_query:
            return super().list(request, *args, **kwargs)

        queryset = self.filter_queryset(self.get_queryset())
        queryset = queryset[:200]
        serializer = self.get_serializer(queryset, many=True)
        return Response(
            OrderedDict(
                [
                    ("count", len(serializer.data)),
                    ("next", None),
                    ("previous", None),
                    ("results", serializer.data),
                ]
            )
        )

    def get_queryset(self):
        """
        Checks if this is a last_updated request and if so annotates and orders
        the queryset by the last_updated field so that the ballots with oldest
        changes appear first.
        This is to help the importer from WCIVF deal with situations where a
        large number of ballots have been updated at the same time e.g. through
        a data migration which saves many or all objects.
        """
        queryset = super().get_queryset()
        if self.request.query_params.get("last_updated"):
            queryset = queryset.with_last_updated()
        return queryset

    def retrieve(self, request, *args, **kwargs):
        """
        A single `Ballot` object
        """
        return super().retrieve(request, *args, **kwargs)

    history_response = openapi.Response("", LoggedActionSerializer)

    @swagger_auto_schema(method="get", responses={200: history_response})
    @action(detail=True, methods=["get"], name="Ballot History")
    def history(self, request, pk=None, **kwargs):
        """
        A list of `LoggedAction` objects for this Ballot

        Returns a list of `LoggedAction` objects filtered by this ballot and
        ordered by the date it was created.

        Typically, this includes locking, unlocking events and entering results

        """
        qs = (
            extra_models.LoggedAction.objects.filter(
                ballot__ballot_paper_id=kwargs["ballot_paper_id"]
            )
            .select_related("ballot", "user")
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


class ElectionTypesList(viewsets.ReadOnlyModelViewSet):
    """
    A list of election types as defined in [EveryElection](https://elections.democracyclub.org.uk/election_types/)
    """

    serializer_class = elections.api.next.serializers.ElectionTypeSerializer
    pagination_class = ResultsSetPagination
    queryset = (
        Election.objects.order_by("for_post_role")
        .distinct("for_post_role")
        .values("slug", "for_post_role")
    )

    def retrieve(self, request, *args, **kwargs):
        """
        A single `ElectionType` object
        """
        return super().retrieve(request, *args, **kwargs)

    @method_decorator(cache_page(60 * 60 * 24))
    def list(self, request, version, format=None):
        qs = self.get_queryset()

        page = self.paginate_queryset(qs)
        if page is not None:
            serializer = elections.api.next.serializers.ElectionTypeSerializer(
                qs, many=True
            )
            return self.get_paginated_response(serializer.data)
