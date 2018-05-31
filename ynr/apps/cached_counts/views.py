from __future__ import unicode_literals

import json

from django.db.models import Count, F
from django.http import HttpResponse
from django.views.generic import TemplateView

from candidates.models import PostExtraElection
from elections.mixins import ElectionMixin
from elections.models import Election
from popolo.models import Membership, Organization
from .models import get_attention_needed_posts


def get_counts(for_json=True):
    election_id_to_candidates = {}
    qs = Membership.objects.filter(
        role=F('post_election__election__candidate_membership_role')
    ).values(
        'post_election__election'
    ).annotate(count=Count('post_election__election'))

    for d in qs:
        election_id_to_candidates[d['post_election__election']] = d['count']

    grouped_elections = Election.group_and_order_elections(for_json=for_json)
    for era_data in grouped_elections:
        for date, elections in era_data['dates'].items():
            for role_data in elections:
                for election_data in role_data['elections']:
                    e = election_data['election']
                    total = election_id_to_candidates.get(e.id, 0)
                    election_counts = {
                        'id': e.slug,
                        'html_id': e.slug.replace('.', '-'),
                        'name': e.name,
                        'total': total,
                    }
                    election_data.update(election_counts)
                    del election_data['election']
    return grouped_elections


class ReportsHomeView(TemplateView):
    template_name = "reports.html"

    def get_context_data(self, **kwargs):
        context = super(ReportsHomeView, self).get_context_data(**kwargs)
        context['all_elections'] = get_counts()
        return context

    def get(self, *args, **kwargs):
        if self.request.GET.get('format') == "json":
            return HttpResponse(
                json.dumps(get_counts(for_json=True)),
                content_type="application/json"
            )
        return super(ReportsHomeView, self).get(*args, **kwargs)


class PartyCountsView(ElectionMixin, TemplateView):
    template_name = "party_counts.html"

    def get_context_data(self, **kwargs):
        context = super(PartyCountsView, self).get_context_data(**kwargs)
        qs = Organization.objects.filter(
            classification='Party',
            memberships_on_behalf_of__post_election__election=self.election_data
        )
        qs = qs.annotate(count=Count('memberships_on_behalf_of'))
        qs = qs.order_by('-count', 'name')

        context['party_counts'] = qs

        return context


class ConstituencyCountsView(ElectionMixin, TemplateView):
    template_name = "constituency_counts.html"

    def get_context_data(self, **kwargs):
        context = super(ConstituencyCountsView, self).get_context_data(**kwargs)
        qs = PostExtraElection.objects.filter(
            election=self.election_data
        ).annotate(count=Count('membership'))
        qs = qs.select_related(
            'postextra__base',
            'election',
        )
        qs = qs.order_by('-count')

        context['post_counts'] = qs
        return context


class AttentionNeededView(TemplateView):
    template_name = "attention_needed.html"

    def get_context_data(self, **kwargs):
        context = super(AttentionNeededView, self).get_context_data(**kwargs)
        context['post_counts'] = get_attention_needed_posts()
        return context
