import json
from os.path import dirname
import subprocess
import sys
from datetime import date, datetime, timedelta
from dateutil import parser

import django
from django.contrib.auth.models import User
from django.db.models import Count, Prefetch, Q
from django.http import HttpResponse, HttpResponsePermanentRedirect
from django.views.generic import View

from rest_framework.reverse import reverse
from rest_framework.viewsets import ViewSet
from rest_framework.response import Response

from api.v09 import serializers
from candidates import models as extra_models
from elections.models import Election
from popolo.models import Membership, Post, Organization
from people.models import PersonImage, Person
from rest_framework import viewsets
from elections.uk.geo_helpers import (
    get_post_elections_from_coords,
    get_post_elections_from_postcode,
)
from ynr_refactoring.views import get_changed_election_slug

from compat import text_type

from api.helpers import ResultsSetPagination


def parse_date(date_text):
    if date_text == "today":
        return date.today()
    try:
        return datetime.strptime(date_text, "%Y-%m-%d").date()
    except ValueError:
        return None


def handle_election(election, request, only_upcoming=False):
    if only_upcoming:
        only_after = date.today()
    else:
        only_after = parse_date(request.GET.get("date_gte", ""))
    if (only_after is not None) and (election.election_date < only_after):
        return False
    if election.current or request.GET.get("all_elections"):
        return True
    return False


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
                pees = get_post_elections_from_coords(coords)
            else:
                pees = get_post_elections_from_postcode(postcode)
        except Exception as e:
            errors = {"error": e.message}

        if errors:
            return HttpResponse(
                json.dumps(errors), status=400, content_type="application/json"
            )

        results = []
        pees = pees.select_related("post", "election")
        for pee in pees:
            results.append(
                {
                    "post_name": pee.post.label,
                    "post_slug": pee.post.slug,
                    "organization": pee.post.organization.name,
                    "election_date": text_type(pee.election.election_date),
                    "election_name": pee.election.name,
                    "election_id": pee.election.slug,
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
                pees = get_post_elections_from_coords(coords)
            else:
                pees = get_post_elections_from_postcode(postcode)
        except Exception as e:
            return self._error(e.message)

        results = []
        pees = pees.select_related("post__organization", "election")
        for pee in pees:
            candidates = []
            for membership in (
                pee.membership_set.filter(
                    post_election__election=pee.election,
                    role=pee.election.candidate_membership_role,
                )
                .prefetch_related(
                    Prefetch(
                        "person__memberships",
                        Membership.objects.select_related(
                            "party", "post", "post_election__election"
                        ),
                    ),
                    "person__images",
                    "person__other_names",
                    "person__contact_details",
                    "person__links",
                    "person__identifiers",
                )
                .select_related("person")
            ):
                candidates.append(
                    serializers.NoVersionPersonSerializer(
                        instance=membership.person,
                        context={"request": request},
                        read_only=True,
                    ).data
                )
            election = {
                "election_date": text_type(pee.election.election_date),
                "election_name": pee.election.name,
                "election_id": pee.election.slug,
                "post": {
                    "post_name": pee.post.label,
                    "post_slug": pee.post.slug,
                    "post_candidates": None,
                },
                "organization": pee.post.organization.name,
                "candidates": candidates,
            }

            results.append(election)

        return Response(results)


class CurrentElectionsView(View):
    http_method_names = ["get"]

    def get(self, request, *args, **kwargs):
        results = {}
        for election in Election.objects.filter(current=True).order_by("id"):
            results[election.slug] = {
                "election_date": text_type(election.election_date),
                "name": election.name,
                "url": reverse(
                    "election-detail",
                    kwargs={"version": "v0.9", "slug": election.slug},
                ),
            }

        res = HttpResponse(json.dumps(results), content_type="application/json")
        res["Expires"] = date.today() + timedelta(days=7)
        return res


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


class PostIDToPartySetView(View):

    http_method_names = ["get"]

    def get(self, request, *args, **kwargs):
        qs = Post.objects.filter(elections__current=True).values_list(
            "slug", "party_set__slug"
        )
        result = dict([(k, v.upper()) for k, v in qs])
        return HttpResponse(json.dumps(result), content_type="application/json")


# Now the django-rest-framework based API views:
class PersonViewSet(viewsets.ModelViewSet):
    def get_queryset(self):
        queryset = Person.objects.prefetch_related(
            Prefetch(
                "memberships",
                Membership.objects.select_related("party", "post"),
            ),
            "memberships__post_election__election",
            "other_names",
            "images",
            "contact_details",
            "links",
            "identifiers",
        ).order_by("id")
        date_qs = self.request.query_params.get("updated_gte", None)
        if date_qs:
            date = parser.parse(date_qs)
            queryset = queryset.filter(
                Q(updated_at__gte=date) | Q(memberships__updated_at__gte=date)
            )
        return queryset

    serializer_class = serializers.PersonSerializer
    pagination_class = ResultsSetPagination


class OrganizationViewSet(viewsets.ModelViewSet):
    queryset = Organization.objects.prefetch_related(
        "contact_details",
        "other_names",
        "sources",
        "links",
        "identifiers",
        "parent",
        "parent",
    ).order_by("id")
    lookup_field = "slug"
    serializer_class = serializers.OrganizationSerializer
    pagination_class = ResultsSetPagination


class PostViewSet(viewsets.ModelViewSet):
    queryset = (
        Post.objects.select_related("organization", "party_set")
        .prefetch_related(
            Prefetch(
                "postextraelection_set",
                extra_models.PostExtraElection.objects.select_related(
                    "election"
                ),
            ),
            Prefetch(
                "memberships",
                Membership.objects.select_related(
                    "person", "party", "post", "post_election__election"
                ),
            ),
        )
        .order_by("id")
    )
    lookup_field = "slug"
    serializer_class = serializers.PostSerializer
    pagination_class = ResultsSetPagination


class ElectionViewSet(viewsets.ModelViewSet):
    lookup_value_regex = "(?!\.json$)[^/]+"
    queryset = Election.objects.order_by("id")
    lookup_field = "slug"
    serializer_class = serializers.ElectionSerializer
    filterset_fields = ("current",)
    pagination_class = ResultsSetPagination

    def dispatch(self, request, *args, **kwargs):
        provided_slug = self.kwargs.get(self.lookup_field)
        if provided_slug:
            new_slug = get_changed_election_slug(provided_slug)
            if new_slug != provided_slug:
                # This is a changed slug
                url = reverse(
                    "election-detail",
                    kwargs={"version": "v0.9", "slug": new_slug},
                )
                if self.kwargs.get("format"):
                    url = "{}.{}".format(url.rstrip("/"), self.kwargs["format"])
                return HttpResponsePermanentRedirect(url)
        return super().dispatch(request, *args, **kwargs)


class PartySetViewSet(viewsets.ModelViewSet):
    queryset = extra_models.PartySet.objects.order_by("id")
    serializer_class = serializers.PartySetSerializer
    pagination_class = ResultsSetPagination


class PostExtraElectionViewSet(viewsets.ModelViewSet):
    queryset = extra_models.PostExtraElection.objects.select_related(
        "election", "post"
    ).order_by("id")
    serializer_class = serializers.PostElectionSerializer
    pagination_class = ResultsSetPagination


class MembershipViewSet(viewsets.ModelViewSet):
    queryset = Membership.objects.order_by("id")
    serializer_class = serializers.MembershipSerializer
    pagination_class = ResultsSetPagination


class LoggedActionViewSet(viewsets.ModelViewSet):
    queryset = extra_models.LoggedAction.objects.order_by("id")
    serializer_class = serializers.LoggedActionSerializer
    pagination_class = ResultsSetPagination


class ExtraFieldViewSet(viewsets.ViewSet):
    def _get_data(self):
        return {
            "id": 1,
            "url": "http://candidates.democracyclub.org.uk/api/v0.9/extra_fields/1/",
            "key": "favourite_biscuits",
            "type": "line",
            "label": "Favourite biscuit 🍪",
            "order": 1,
        }

    def list(self, request, *args, **kwargs):
        data = {
            "count": 1,
            "next": None,
            "previous": None,
            "results": [self._get_data()],
        }
        return Response(data)

    def retrieve(self, request, pk=None):
        return Response(self._get_data())


class PersonRedirectViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = extra_models.PersonRedirect.objects.order_by("id")
    lookup_field = "old_person_id"
    serializer_class = serializers.PersonRedirectSerializer
    pagination_class = ResultsSetPagination
