import json

from django.http import HttpResponse
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
from django.views import View
from rest_framework.decorators import action
from rest_framework import viewsets
from rest_framework.response import Response
from six import text_type

import elections.api.next.serializers
from api.next.views import ResultsSetPagination
from candidates import models as extra_models
from candidates.api.next.serializers import LoggedActionSerializer
from elections.models import Election
from elections.uk.geo_helpers import (
    get_ballots_from_coords,
    get_ballots_from_postcode,
)
from elections.filters import BallotFilter, election_types_choices


class UpcomingElectionsView(View):

    http_method_names = ["get"]

    def get(self, request, *args, **kwargs):
        postcode = request.GET.get("postcode", None)
        coords = request.GET.get("coords", None)

        # TODO: postcode may not make sense everywhere
        errors = None
        if not postcode and not coords:
            errors = {"error": "Postcode or Co-ordinates required"}

        try:
            if coords:
                ballots = get_ballots_from_coords(coords)
            else:
                ballots = get_ballots_from_postcode(postcode)
        except Exception as e:
            errors = {"error": e.message}

        if errors:
            return HttpResponse(
                json.dumps(errors), status=400, content_type="application/json"
            )

        results = []
        ballots = ballots.select_related("post", "election")
        for ballot in ballots:
            results.append(
                {
                    "post_name": ballot.post.label,
                    "post_slug": ballot.post.slug,
                    "organization": ballot.post.organization.name,
                    "election_date": text_type(ballot.election.election_date),
                    "election_name": ballot.election.name,
                    "election_id": ballot.election.slug,
                }
            )

        return HttpResponse(
            json.dumps(results), content_type="application/json"
        )


class ElectionViewSet(viewsets.ModelViewSet):
    lookup_value_regex = r"(?!\.json$)[^/]+"
    queryset = Election.objects.order_by("id")
    lookup_field = "slug"
    serializer_class = elections.api.next.serializers.ElectionSerializer
    filterset_fields = ("current",)
    pagination_class = ResultsSetPagination


class BallotViewSet(viewsets.ReadOnlyModelViewSet):
    lookup_field = "ballot_paper_id"
    lookup_value_regex = "[^/]+"
    queryset = (
        extra_models.Ballot.objects.select_related("election", "post")
        .prefetch_related("membership_set")
        .order_by("-election__election_date", "ballot_paper_id")
    )
    serializer_class = elections.api.next.serializers.BallotSerializer
    pagination_class = ResultsSetPagination

    filterset_class = BallotFilter

    @action(detail=True, methods=["get"], name="Ballot History")
    def history(self, request, pk=None, **kwargs):
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


class ElectionTypesList(viewsets.ViewSet):
    """
    Return a list of all election types, used for
    discovery of filter values in the `ballots` endpoint.
    """

    @method_decorator(cache_page(60 * 60 * 24))
    def list(self, request, version):
        return Response(election_types_choices())
