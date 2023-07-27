import csv

from candidates.filters import (
    LoggedActionRecentChangesFilter,
    recent_changes_filter_shortcuts,
)
from django.contrib.auth.models import User
from django.core.paginator import EmptyPage, PageNotAnInteger, Paginator
from django.db.models import Count
from django.http import HttpResponse
from django.views.generic import TemplateView, View

from .mixins import ContributorsMixin


class RecentChangesView(ContributorsMixin, TemplateView):
    template_name = "candidates/recent-changes.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        actions = self.get_recent_changes_queryset()
        filter = LoggedActionRecentChangesFilter(
            self.request.GET, queryset=actions
        )
        paginator = Paginator(filter.qs, 50)
        page = self.request.GET.get("page")
        context["filter"] = filter
        context["shortcuts"] = recent_changes_filter_shortcuts(self.request)
        try:
            context["actions"] = paginator.page(page)
        except PageNotAnInteger:
            context["actions"] = paginator.page(1)
        except EmptyPage:
            context["actions"] = paginator.page(paginator.num_pages)
        return context


class LeaderboardView(ContributorsMixin, TemplateView):
    template_name = "candidates/leaderboard.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["leaderboards"] = self.get_leaderboards()
        return context


class UserContributions(View):

    http_method_names = ["get"]

    def get(self, request, *args, **kwargs):
        response = HttpResponse(content_type="text/csv")
        response[
            "Content-Disposition"
        ] = 'attachment; filename="contributions.csv"'
        headers = ["rank", "username", "contributions"]
        writer = csv.DictWriter(response, fieldnames=headers)
        writer.writerow({k: k for k in headers})

        qs = (
            User.objects.extra(
                select={"case_insensitive_username": "lower(username)"}
            )
            .annotate(edit_count=Count("loggedaction"))
            .order_by("-edit_count", "case_insensitive_username")
        )

        for i, user in enumerate(qs):
            writer.writerow(
                {
                    "rank": str(i),
                    "username": user.username,
                    "contributions": user.edit_count,
                }
            )
        return response
