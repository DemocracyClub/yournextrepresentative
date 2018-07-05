import json
from os.path import dirname
import subprocess
import sys
from datetime import date, datetime, timedelta
from dateutil import parser

import django
from django.contrib.auth.models import User
from django.db.models import Count, Prefetch, Q
from django.http import HttpResponse
from django.views.generic import View

from rest_framework.reverse import reverse
from rest_framework.viewsets import ViewSet
from rest_framework.response import Response

from images.models import Image
from candidates import serializers
from candidates import models as extra_models
from elections.models import Election
from popolo.models import Membership, Person, Post
from rest_framework import pagination, viewsets
from elections.uk.geo_helpers import (
    get_post_elections_from_coords, get_post_elections_from_postcode)

from compat import text_type


def parse_date(date_text):
    if date_text == 'today':
        return date.today()
    try:
        return datetime.strptime(date_text, '%Y-%m-%d').date()
    except ValueError:
        return None


def handle_election(election, request, only_upcoming=False):
    if only_upcoming:
        only_after = date.today()
    else:
        only_after = parse_date(request.GET.get('date_gte', ''))
    if (only_after is not None) and (election.election_date < only_after):
        return False
    if election.current or request.GET.get('all_elections'):
        return True
    return False


class UpcomingElectionsView(View):

    http_method_names = ['get']

    def get(self, request, *args, **kwargs):
        postcode = request.GET.get('postcode', None)
        coords = request.GET.get('coords', None)

        # TODO: postcode may not make sense everywhere
        errors = None
        if not postcode and not coords:
            errors = {
                'error': 'Postcode or Co-ordinates required'
            }

        try:
            if coords:
                pees = get_post_elections_from_coords(coords)
            else:
                pees = get_post_elections_from_postcode(postcode)
        except Exception as e:
            errors = {
                'error': e.message
            }

        if errors:
            return HttpResponse(
                json.dumps(errors), status=400, content_type='application/json'
            )

        results = []
        pees = pees.select_related('postextra__base', 'election')
        for pee in pees:
            results.append({
                'post_name': pee.postextra.base.label,
                'post_slug': pee.postextra.slug,
                'organization': pee.postextra.base.organization.name,
                'election_date': text_type(pee.election.election_date),
                'election_name': pee.election.name,
                'election_id': pee.election.slug
            })

        return HttpResponse(
            json.dumps(results), content_type='application/json'
        )


class CandidatesAndElectionsForPostcodeViewSet(ViewSet):
    # This re-produces a lot of UpcomingElectionsView, but the output
    # is different enough to justify it being a different view

    http_method_names = ['get']

    def _error(self, error_msg):
        return Response({'error': error_msg}, status=400,)

    def list(self, request, *args, **kwargs):
        postcode = request.GET.get('postcode', None)
        coords = request.GET.get('coords', None)

        # TODO: postcode may not make sense everywhere
        errors = None
        if not postcode and not coords:
            return self._error('Postcode or Co-ordinates required')

        try:
            if coords:
                pees = get_post_elections_from_coords(coords)
            else:
                pees = get_post_elections_from_postcode(postcode)
        except Exception as e:
            return self._error(e.message)

        results = []
        pees = pees.select_related(
            'postextra__base__organization',
            'election'
        )
        for pee in pees:
            candidates = []
            for membership in pee.membership_set.filter(
                    post_election__election=pee.election,
                    role=pee.election.candidate_membership_role) \
                    .prefetch_related(
                        Prefetch(
                            'person__memberships',
                            Membership.objects.select_related(
                                'on_behalf_of__extra',
                                'organization__extra',
                                'post__extra',
                                'post_election__election',
                            )
                        ),
                        Prefetch(
                            'person__extra__images',
                            Image.objects.select_related('extra__uploading_user')
                        ),
                        'person__other_names',
                        'person__contact_details',
                        'person__links',
                        'person__identifiers',
                        'person__extra_field_values',
                    ) \
                    .select_related('person__extra'):
                candidates.append(
                    serializers.NoVersionPersonSerializer(
                        instance=membership.person,
                        context={
                            'request': request,
                        },
                        read_only=True,
                    ).data
                )
            election = {
                'election_date': text_type(pee.election.election_date),
                'election_name': pee.election.name,
                'election_id': pee.election.slug,
                'post': {
                    'post_name': pee.postextra.base.label,
                    'post_slug': pee.postextra.slug,
                    'post_candidates': None
                },
                'organization': pee.postextra.base.organization.name,
                'candidates': candidates,

            }

            results.append(election)

        return Response(results)


class CurrentElectionsView(View):
    http_method_names = ['get']

    def get(self, request, *args, **kwargs):
        results = {}
        for election in Election.objects.filter(current=True).order_by('id'):
            results[election.slug] = {
                'election_date': text_type(election.election_date),
                'name': election.name,
                'url': reverse('election-detail', kwargs={
                    'version': 'v0.9',
                    'slug': election.slug})
            }

        res = HttpResponse(
            json.dumps(results), content_type='application/json',
            )
        res['Expires'] = date.today() + timedelta(days=7)
        return res


class VersionView(View):

    http_method_names = ['get']

    def get(self, request, *args, **kwargs):
        result = {
            'python_version': sys.version,
            'django_version': django.get_version(),
            'interesting_user_actions': extra_models.LoggedAction.objects \
                .exclude(action_type='set-candidate-not-elected') \
                .count(),
            'users_who_have_edited': User.objects \
                .annotate(edit_count=Count('loggedaction')) \
                .filter(edit_count__gt=0).count()
        }
        # Try to get the object name of HEAD from git:
        try:
            git_version = subprocess.check_output(
                ['git', 'rev-parse', '--verify', 'HEAD'],
                cwd=dirname(__file__),
                universal_newlines=True
            ).strip()
            result['git_version'] = git_version
        except (OSError, subprocess.CalledProcessError):
            pass
        return HttpResponse(
            json.dumps(result), content_type='application/json'
        )


class PostIDToPartySetView(View):

    http_method_names = ['get']

    def get(self, request, *args, **kwargs):
        result = dict(
            extra_models.PostExtra.objects.filter(elections__current=True) \
               .values_list('slug', 'party_set__slug')
        )
        return HttpResponse(
            json.dumps(result), content_type='application/json'
        )

class AllPartiesJSONView(View):

    http_method_names = ['get']

    def get(self, request, *args, **kwargs):
        partyset = self.request.GET.get('partyset', None)
        status_code = 200
        if not partyset:
            ret = {'error': 'Please provide a partyset as a GET param'}

        ps = extra_models.PartySet.objects.get(slug=partyset)
        ret = {
            'items': []
        }
        qs = ps.party_choices(
            exclude_deregistered=True,
            include_description_ids=True
        )
        for party in qs:
            item = {}
            if type(party[1]) == list:
                item['text'] = party[0]
                item['children'] = []
                for child in party[1]:
                    item['children'].append({
                        'id': child[0],
                        'text': child[1],
                    })
            else:
                item['id'] = party[0]
                item['text'] = party[1]

            ret['items'].append(item)

        return HttpResponse(
            json.dumps(ret),
            content_type='application/json',
            status=status_code
        )


# Now the django-rest-framework based API views:

class ResultsSetPagination(pagination.PageNumberPagination):
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 200


class PersonViewSet(viewsets.ModelViewSet):

    def get_queryset(self):
        queryset = Person.objects \
            .select_related('extra') \
            .prefetch_related(
                Prefetch(
                    'memberships',
                    Membership.objects.select_related(
                        'on_behalf_of__extra',
                        'organization__extra',
                        'post__extra',
                    )
                ),
                'memberships__post_election__election',
                'memberships__organization__extra',
                'extra__images',
                'other_names',
                'contact_details',
                'links',
                'identifiers',
            ) \
            .order_by('id')
        date_qs = self.request.query_params.get('updated_gte', None)
        if date_qs:
            date = parser.parse(date_qs)
            queryset = queryset.filter(
                Q(updated_at__gte=date)
                |
                Q(memberships__updated_at__gte=date)

            )
        return queryset

    serializer_class = serializers.PersonSerializer
    pagination_class = ResultsSetPagination


class OrganizationViewSet(viewsets.ModelViewSet):
    queryset = extra_models.OrganizationExtra.objects \
        .select_related('base') \
        .prefetch_related(
            'images',
            'images__extra',
            'base__contact_details',
            'base__other_names',
            'base__sources',
            'base__links',
            'base__identifiers',
            'base__parent',
            'base__parent__extra',
        ) \
        .order_by('base__id')
    lookup_field = 'slug'
    serializer_class = serializers.OrganizationExtraSerializer
    pagination_class = ResultsSetPagination


class PostViewSet(viewsets.ModelViewSet):
    queryset = extra_models.PostExtra.objects \
        .select_related(
            'base__organization__extra',
            'party_set',
        ) \
        .prefetch_related(
            Prefetch(
                'postextraelection_set',
                extra_models.PostExtraElection.objects \
                    .select_related('election')
            ),
            Prefetch(
                'base__memberships',
                Membership.objects.select_related(
                    'person',
                    'on_behalf_of__extra',
                    'organization__extra',
                    'post__extra',
                    'post_election__election',
                )
            )
        ) \
        .order_by('base__id')
    lookup_field = 'slug'
    serializer_class = serializers.PostExtraSerializer
    pagination_class = ResultsSetPagination


class ElectionViewSet(viewsets.ModelViewSet):
    lookup_value_regex="(?!\.json$)[^/]+"
    queryset = Election.objects.order_by('id')
    lookup_field = 'slug'
    serializer_class = serializers.ElectionSerializer
    filter_fields = ('current',)
    pagination_class = ResultsSetPagination


class PartySetViewSet(viewsets.ModelViewSet):
    queryset = extra_models.PartySet.objects.order_by('id')
    serializer_class = serializers.PartySetSerializer
    pagination_class = ResultsSetPagination


class ImageViewSet(viewsets.ModelViewSet):
    queryset = Image.objects.order_by('id')
    serializer_class = serializers.ImageSerializer
    pagination_class = ResultsSetPagination


class PostExtraElectionViewSet(viewsets.ModelViewSet):
    queryset = extra_models.PostExtraElection.objects \
        .select_related('election', 'postextra') \
        .order_by('id')
    serializer_class = serializers.PostElectionSerializer
    pagination_class = ResultsSetPagination


class MembershipViewSet(viewsets.ModelViewSet):
    queryset = Membership.objects.order_by('id')
    serializer_class = serializers.MembershipSerializer
    pagination_class = ResultsSetPagination


class LoggedActionViewSet(viewsets.ModelViewSet):
    queryset = extra_models.LoggedAction.objects.order_by('id')
    serializer_class = serializers.LoggedActionSerializer
    pagination_class = ResultsSetPagination


class ExtraFieldViewSet(viewsets.ModelViewSet):
    queryset = extra_models.ExtraField.objects.order_by('id')
    serializer_class = serializers.ExtraFieldSerializer
    pagination_class = ResultsSetPagination


class ComplexPopoloFieldViewSet(viewsets.ModelViewSet):
    queryset = extra_models.ComplexPopoloField.objects.order_by('id')
    serializer_class = serializers.ComplexPopoloFieldSerializer
    pagination_class = ResultsSetPagination

class PersonRedirectViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = extra_models.PersonRedirect.objects.order_by('id')
    lookup_field = 'old_person_id'
    serializer_class = serializers.PersonRedirectSerializer
    pagination_class = ResultsSetPagination
