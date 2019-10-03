import json
import subprocess
import sys
from datetime import date, datetime
from os.path import dirname

import django
from dateutil import parser
from django.contrib.auth.models import User
from django.db.models import Count, Prefetch, Q
from django.http import HttpResponse
from django.views.generic import View
from rest_framework import pagination, viewsets
from rest_framework.response import Response
from rest_framework.viewsets import ViewSet

import candidates.serializers
import elections.serializers
import parties.serializers
import people.serializers
import popolo.serializers
from api.next import serializers
from candidates import models as extra_models
from compat import text_type
from elections.models import Election
from elections.uk.geo_helpers import (
    get_ballots_from_coords,
    get_ballots_from_postcode,
)
from parties.models import Party
from people.models import Person, PersonImage
from popolo.models import Membership, Organization, Post


def parse_date(date_text):
    if date_text == "today":
        return date.today()
    try:
        return datetime.strptime(date_text, "%Y-%m-%d").date()
    except ValueError:
        return None


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


class CandidatesAndElectionsForPostcodeViewSet(ViewSet):
    # This re-produces a lot of UpcomingElectionsView, but the output
    # is different enough to justify it being a different view

    http_method_names = ["get"]

    def _error(self, error_msg):
        return Response({"error": error_msg}, status=400)

    def list(self, request, *args, **kwargs):
        postcode = request.GET.get("postcode", None)
        coords = request.GET.get("coords", None)

        # TODO: postcode may not make sense everywhere
        errors = None
        if not postcode and not coords:
            return self._error("Postcode or Co-ordinates required")

        try:
            if coords:
                ballots = get_ballots_from_coords(coords)
            else:
                ballots = get_ballots_from_postcode(postcode)
        except Exception as e:
            return self._error(e.message)

        results = []
        ballots = ballots.select_related("post__organization", "election")
        for ballot in ballots:
            candidates = []
            for membership in (
                ballot.membership_set.filter(
                    ballot__election=ballot.election,
                    role=ballot.election.candidate_membership_role,
                )
                .prefetch_related(
                    Prefetch(
                        "person__memberships",
                        Membership.objects.select_related(
                            "party", "post", "ballot__election"
                        ),
                    ),
                    Prefetch(
                        "person__images",
                        PersonImage.objects.select_related("uploading_user"),
                    ),
                    "person__other_names",
                )
                .select_related("person")
            ):
                candidates.append(
                    people.serializers.NoVersionPersonSerializer(
                        instance=membership.person,
                        context={"request": request},
                        read_only=True,
                    ).data
                )
            election = {
                "election_date": text_type(ballot.election.election_date),
                "election_name": ballot.election.name,
                "election_id": ballot.election.slug,
                "post": {
                    "post_name": ballot.post.label,
                    "post_slug": ballot.post.slug,
                    "post_candidates": None,
                },
                "organization": ballot.post.organization.name,
                "candidates": candidates,
            }

            results.append(election)

        return Response(results)


class VersionView(View):

    http_method_names = ["get"]

    def get(self, request, *args, **kwargs):
        result = {
            "python_version": sys.version,
            "django_version": django.get_version(),
            "interesting_user_actions": extra_models.LoggedAction.objects.exclude(
                action_type="set-candidate-not-elected"
            ).count(),
            "users_who_have_edited": User.objects.annotate(
                edit_count=Count("loggedaction")
            )
            .filter(edit_count__gt=0)
            .count(),
        }
        # Try to get the object name of HEAD from git:
        try:
            git_version = subprocess.check_output(
                ["git", "rev-parse", "--verify", "HEAD"],
                cwd=dirname(__file__),
                universal_newlines=True,
            ).strip()
            result["git_version"] = git_version
        except (OSError, subprocess.CalledProcessError):
            pass
        return HttpResponse(json.dumps(result), content_type="application/json")


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


# Now the django-rest-framework based API views:
class ResultsSetPagination(pagination.PageNumberPagination):
    page_size = 10
    page_size_query_param = "page_size"
    max_page_size = 200


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


class OrganizationViewSet(viewsets.ModelViewSet):

    queryset = (
        Organization.objects.prefetch_related(
            "contact_details",
            "other_names",
            "sources",
            "identifiers",
            "parent",
            "parent",
        ).order_by("id")
    ).exclude(classification="Party")
    lookup_field = "slug"
    serializer_class = serializers.OrganizationSerializer
    pagination_class = ResultsSetPagination


class PostViewSet(viewsets.ModelViewSet):
    queryset = (
        Post.objects.select_related("organization", "party_set")
        .prefetch_related(
            Prefetch(
                "ballot_set",
                extra_models.Ballot.objects.select_related("election"),
            ),
            Prefetch(
                "memberships",
                Membership.objects.select_related(
                    "person", "party", "post", "ballot__election"
                ),
            ),
        )
        .order_by("id")
    )
    lookup_field = "slug"
    serializer_class = popolo.serializers.PostSerializer
    pagination_class = ResultsSetPagination


class ElectionViewSet(viewsets.ModelViewSet):
    lookup_value_regex = r"(?!\.json$)[^/]+"
    queryset = Election.objects.order_by("id")
    lookup_field = "slug"
    serializer_class = elections.serializers.ElectionSerializer
    filterset_fields = ("current",)
    pagination_class = ResultsSetPagination


class PostExtraElectionViewSet(viewsets.ModelViewSet):
    queryset = extra_models.Ballot.objects.select_related(
        "election", "post"
    ).order_by("id")
    serializer_class = elections.serializers.PostElectionSerializer
    pagination_class = ResultsSetPagination


class LoggedActionViewSet(viewsets.ModelViewSet):
    queryset = extra_models.LoggedAction.objects.order_by("id")
    serializer_class = candidates.serializers.LoggedActionSerializer
    pagination_class = ResultsSetPagination


class PersonRedirectViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = extra_models.PersonRedirect.objects.order_by("id")
    lookup_field = "old_person_id"
    serializer_class = people.serializers.PersonRedirectSerializer
    pagination_class = ResultsSetPagination
