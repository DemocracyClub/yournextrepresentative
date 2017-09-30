# -*- coding: utf-8 -*-

"""
NOTE: Both views in this file are deprecated and redirects should be found
      for them. It's not obvious where the area view should redirect to
      at the moment
"""

from __future__ import unicode_literals

from django.db.models import Prefetch
from django.http import Http404, HttpResponseBadRequest
from django.views.generic import TemplateView
from django.utils.translation import ugettext as _

from candidates.models import AreaExtra, PostExtra, MembershipExtra
from candidates.models.auth import get_edits_allowed, is_post_locked

from elections.models import Election

from ..forms import NewPersonForm, ToggleLockForm
from .helpers import (
    split_candidacies, group_candidates_by_party,
    get_person_form_fields, split_by_elected
)


class AreasView(TemplateView):
    """
    This view should be considered deprecated, but is here in order to maintain
    URLs that might exist in the wild. It will get less useful over time as:

    1. Even a well formed URL will only return information for posts
       with current elections
    2. New posts might have different IDs as we can't rely on GSS codes for
       new areas
    3. A postcode more in keeping with the _intent_ of this view – but the
       conversion of postcode to areas was previously done elsewhere
    """

    template_name = 'candidates/areas.html'

    def get(self, request, *args, **kwargs):
        self.types_and_areas = []
        for type_and_area in kwargs['type_and_area_ids'].split(','):
            if '--' not in type_and_area:
                message = _("Malformed type and area: '{0}'")
                return HttpResponseBadRequest(message.format(type_and_area))
            self.types_and_areas.append(type_and_area.split('--', 1))
        response = super(AreasView, self).get(request, *args, **kwargs)
        return response

    def get_context_data(self, **kwargs):
        context = super(AreasView, self).get_context_data(**kwargs)
        all_area_names = set()
        context['posts'] = []
        any_area_found = False
        no_data_areas = []
        posts_seen = set()
        for area_type_code, area_id in self.types_and_areas:
            area_extras = AreaExtra.objects \
                .select_related('base', 'type') \
                .prefetch_related('base__posts') \
                .filter(base__identifier=area_id)
            if area_extras.exists():
                any_area_found = True
            else:
                continue

            for area_extra in area_extras:
                area = area_extra.base
                all_area_names.add(area.name)
                for post in area.posts.all():
                    post_extra = post.extra
                    try:
                        election = post_extra.elections.get(current=True)
                    except Election.DoesNotExist:
                        continue
                    if post.id in posts_seen:
                        continue
                    else:
                        posts_seen.add(post.id)
                    locked = is_post_locked(post, election)
                    extra_qs = MembershipExtra.objects.select_related('election')
                    current_candidacies, _ = split_candidacies(
                        election,
                        post.memberships.prefetch_related(
                            Prefetch('extra', queryset=extra_qs)
                        ).select_related(
                            'person', 'person__extra', 'on_behalf_of',
                            'on_behalf_of__extra', 'organization'
                        ).all()
                    )
                    elected_candidacies, unelected_candidacies = split_by_elected(
                        election,
                        current_candidacies,
                    )
                    elected_candidacies = group_candidates_by_party(
                        election,
                        elected_candidacies,
                    )
                    unelected_candidacies = group_candidates_by_party(
                        election,
                        unelected_candidacies,
                    )
                    post_context = {
                        'election': election.slug,
                        'election_data': election,
                        'post_data': {
                            'id': post.extra.slug,
                            'label': post.label,
                        },
                        'candidates_locked': locked,
                        'lock_form': ToggleLockForm(
                            initial={
                                'post_id': post.extra.slug,
                                'lock': not locked
                            },
                        ),
                        'candidate_list_edits_allowed':
                        get_edits_allowed(self.request.user, locked),
                        'has_elected': \
                            len(elected_candidacies['parties_and_people']) > 0,
                        'elected': elected_candidacies,
                        'unelected': unelected_candidacies,
                        'add_candidate_form': NewPersonForm(
                            election=election.slug,
                            initial={
                                ('constituency_' + election.slug): post_extra.slug,
                                ('standing_' + election.slug): 'standing',
                            },
                            hidden_post_widget=True,
                        ),
                    }

                    post_context = get_person_form_fields(
                        post_context,
                        post_context['add_candidate_form']
                    )

                    context['posts'].append(post_context)

        context['no_data_areas'] = no_data_areas

        if not any_area_found:
            raise Http404("No such areas found")
        context['all_area_names'] = ' — '.join(all_area_names)
        context['suppress_official_documents'] = True
        return context


class PostsOfTypeView(TemplateView):
    """
    TODO: Move this out of the candidates app in to a posts app
    TODO: convert this view in to a redirect to EveryElection?

    It's not obvious that this view is needed or of use to anyone.

    It replaces `AreasOfTypeView` – a view that listed areas of a type,
    where the type was a type code from mySociety's MaPit install.

    Since "Areas" as a concept have been deprecated in YNR this view offers:

    1. A view of posts that have this type ID (post slugs start with the type)
    2. A message explaining that this view isn't a useful thing to
       use (for people who might have bookmarked the URL)

    This view should be removed in the future if it's not providing anything
    useful. It shouldn't be linked to unless it's actually useful.
    """
    template_name = 'candidates/posts-of-type.html'

    def get_context_data(self, **kwargs):
        context = super(PostsOfTypeView, self).get_context_data(**kwargs)
        post_type = context['post_type']

        posts_qs = PostExtra.objects.filter(slug__startswith=post_type)
        posts_qs = posts_qs.select_related('base').order_by('base__label')
        context['posts'] = posts_qs
        return context
