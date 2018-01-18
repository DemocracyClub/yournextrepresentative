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
        """
        Set a HTTP 410: GONE status to indicate that this URL shouldn't be
        indexed any more.
        """
        context = self.get_context_data(**kwargs)
        return self.render_to_response(context, status=410)


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
