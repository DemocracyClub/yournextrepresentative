from __future__ import unicode_literals

import csv

from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.core.urlresolvers import reverse
from django.db.models import Count
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import get_object_or_404
from django.utils.translation import ugettext_lazy as _
from django.views.generic import TemplateView, View

from ..forms import ChangeReviewedForm
from .mixins import ContributorsMixin
from ..models import ChangeReviewed, LoggedAction

from popolo.models import Person


class RecentChangesView(ContributorsMixin, TemplateView):
    template_name = 'candidates/recent-changes.html'

    def get_context_data(self, **kwargs):
        context = super(RecentChangesView, self).get_context_data(**kwargs)
        actions = self.get_recent_changes_queryset()
        paginator = Paginator(actions, 50)
        page = self.request.GET.get('page')
        try:
            context['actions'] = paginator.page(page)
        except PageNotAnInteger:
            context['actions'] = paginator.page(1)
        except EmptyPage:
            context['actions'] = paginator.page(paginator.num_pages)
        return context


class MarkChangeAsReviewedView(View):
    def post(self, request, *args, **kwargs):
        form = ChangeReviewedForm(data=self.request.POST)

        if form.is_valid():
            person_id = form.cleaned_data['person_id']
            logged_action_id = form.cleaned_data['logged_action_id']
            reviewer_id = request.user.id

            ChangeReviewed.objects.create(
                person=get_object_or_404(Person, pk=person_id),
                logged_action=get_object_or_404(LoggedAction, pk=logged_action_id),
                reviewer=get_object_or_404(User, pk=reviewer_id),
            )
            return HttpResponseRedirect(
                reverse('recent-changes')
            )
        else:
            message = _('Invalid data POSTed to MarkChangeAsReviewedView')
            raise ValidationError(message)


class LeaderboardView(ContributorsMixin, TemplateView):
    template_name = 'candidates/leaderboard.html'

    def get_context_data(self, **kwargs):
        context = super(LeaderboardView, self).get_context_data(**kwargs)
        context['leaderboards'] = self.get_leaderboards()
        return context


class UserContributions(View):

    http_method_names = ['get']

    def get(self, request, *args, **kwargs):
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = \
            'attachment; filename="contributions.csv"'
        headers = ['rank', 'username', 'contributions']
        writer = csv.DictWriter(response, fieldnames=headers)
        writer.writerow({k: k for k in headers})
        for i, user in enumerate(User.objects.annotate(
                edit_count=Count('loggedaction')
        ).order_by('-edit_count', 'username')):
            writer.writerow({
                'rank': str(i),
                'username': user.username,
                'contributions': user.edit_count
            })
        return response
