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


# Now the django-rest-framework based API views:
class ResultsSetPagination(pagination.PageNumberPagination):
    page_size = 10
    page_size_query_param = "page_size"
    max_page_size = 200


class OrganizationViewSet(viewsets.ModelViewSet):

    queryset = (
        Organization.objects.all()
        .order_by("slug")
        .exclude(classification="Party")
    )
    lookup_field = "slug"
    serializer_class = serializers.OrganizationSerializer
    pagination_class = ResultsSetPagination


class LoggedActionViewSet(viewsets.ModelViewSet):
    queryset = extra_models.LoggedAction.objects.order_by("id")
    serializer_class = candidates.serializers.LoggedActionSerializer
    pagination_class = ResultsSetPagination
