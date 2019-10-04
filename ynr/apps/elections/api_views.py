import json

from django.http import HttpResponse
from django.views import View
from rest_framework import viewsets
from six import text_type

import elections.serializers
from api.next.views import ResultsSetPagination
from candidates import models as extra_models
from elections.models import Election
from elections.uk.geo_helpers import (
    get_ballots_from_coords,
    get_ballots_from_postcode,
)
from elections.filters import BallotFilter


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
    serializer_class = elections.serializers.ElectionSerializer
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
    serializer_class = elections.serializers.BallotSerializer
    pagination_class = ResultsSetPagination

    filterset_class = BallotFilter
