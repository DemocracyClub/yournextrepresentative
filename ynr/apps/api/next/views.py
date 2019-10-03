import json
import subprocess
import sys
from datetime import date, datetime
from os.path import dirname

import django
from django.contrib.auth.models import User
from django.db.models import Count, Prefetch
from django.http import HttpResponse
from django.views.generic import View
from rest_framework import pagination, viewsets

import candidates.serializers
import popolo.serializers
from api.next import serializers
from candidates import models as extra_models
from popolo.models import Membership, Organization, Post


def parse_date(date_text):
    if date_text == "today":
        return date.today()
    try:
        return datetime.strptime(date_text, "%Y-%m-%d").date()
    except ValueError:
        return None


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


# Now the django-rest-framework based API views:
class ResultsSetPagination(pagination.PageNumberPagination):
    page_size = 10
    page_size_query_param = "page_size"
    max_page_size = 200


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


class LoggedActionViewSet(viewsets.ModelViewSet):
    queryset = extra_models.LoggedAction.objects.order_by("id")
    serializer_class = candidates.serializers.LoggedActionSerializer
    pagination_class = ResultsSetPagination
