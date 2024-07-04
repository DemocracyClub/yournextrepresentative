"""
Views just for recording winners in parl. elections.

Not really useful for any other sort of election.

"""

from urllib.parse import urlencode

import django_filters
from braces.views import LoginRequiredMixin
from candidates.models import LoggedAction
from candidates.models.db import ActionType, EditType
from candidates.views import get_change_metadata, get_client_ip
from data_exports.filters import ELECTED_CHOICES
from data_exports.models import MaterializedMemberships
from django.contrib import messages
from django.db.models import (
    Count,
    Exists,
    OuterRef,
)
from django.db.models.functions import Coalesce
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.views.generic import TemplateView
from elections.filters import DSLinkWidget, region_choices
from popolo.models import Membership
from uk_results.models import SuggestedWinner
from utils.db import LastWord, NullIfBlank


def filter_shortcuts(request):
    shortcut_list = [
        {
            "name": "part_entered",
            "label": "Part entered",
            "query": {"part_entered": ["true"]},
        },
        {
            "name": "needs_entering",
            "label": "Needs entering",
            "query": {"part_entered": ["false"], "elected": ["False"]},
        },
    ]

    query = dict(request.GET)
    shortcuts = {"list": shortcut_list}
    for shortcut in shortcuts["list"]:
        shortcut["querystring"] = urlencode(shortcut["query"], doseq=True)
        if shortcut["query"] == query:
            shortcut["active"] = True
            shortcuts["active"] = shortcut
    return shortcuts


class MembershipsFilter(django_filters.FilterSet):
    filter_by_region = django_filters.ChoiceFilter(
        widget=DSLinkWidget(),
        method="region_filter",
        label="Filter by region",
        choices=region_choices,
    )
    part_entered = django_filters.ChoiceFilter(
        widget=DSLinkWidget(),
        method="part_entered_filter",
        label="Part entered",
        choices=(("true", "Yes"),),
    )

    elected = django_filters.ChoiceFilter(
        field_name="elected",
        label="Elected",
        choices=ELECTED_CHOICES,
        method="elected_filter",
        empty_label="All",
        widget=DSLinkWidget(),
    )

    def region_filter(self, queryset, name, value):
        """
        Filter queryset by region using the NUTS1 code
        """
        return queryset.filter(ballot_paper__tags__NUTS1__key__in=[value])

    def part_entered_filter(self, queryset, name, value):
        """
        Filter queryset by region using the NUTS1 code
        """
        if value == "true":
            return queryset.filter(suggested_ballot=True)
        return queryset

    def elected_filter(self, queryset, name, value):
        if value == "True":
            return queryset.filter(has_winner=True)
        if value == "False":
            return queryset.filter(has_winner=False)
        return queryset


class ParlBallotsWinnerEntryView(LoginRequiredMixin, TemplateView):
    template_name = "uk_results/parl_mark_winners.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        suggested_subquery = (
            Membership.objects.annotate(suggested=Count("suggested_winners"))
            .filter(
                ballot__ballot_paper_id=OuterRef("ballot_paper"),
                suggested=1,
                elected=False,
            )
            .only("pk")
        )
        elected_subquery = MaterializedMemberships.objects.filter(
            ballot_paper=OuterRef("ballot_paper"),
            elected=True,
        ).only("pk")

        memberships = (
            MaterializedMemberships.objects.filter(
                ballot_paper__election__slug="parl.2024-07-04"
            )
            .select_related("ballot_paper__post")
            .annotate(suggested_ballot=Exists(suggested_subquery))
            .annotate(has_winner=Exists(elected_subquery))
            .annotate(last_name=LastWord("person_name"))
            .annotate(
                name_for_ordering=Coalesce(
                    NullIfBlank("person__sort_name"), "last_name"
                )
            )
            .order_by("ballot_paper_id", "name_for_ordering")
        )

        f = MembershipsFilter(self.request.GET, memberships)

        context["filter"] = f
        context["memberships"] = f.qs
        context["shortcuts"] = filter_shortcuts(self.request)
        context["sort_by"] = self.request.GET.get("sort_by", "time")

        return context

    def post(self, *args, **kwargs):
        membership_id = self.request.POST.get("membership_id")
        if not membership_id:
            return HttpResponseRedirect(reverse("parl_24_winner_form"))
        membership = Membership.objects.get(pk=membership_id)

        unset = bool(self.request.POST.get("unset", False))
        is_elected = not unset
        SuggestedWinner.record_suggestion(
            self.request.user, membership, is_elected=is_elected
        )

        membership.refresh_from_db()

        action_type = ActionType.ENTERED_RESULTS_DATA
        message = f"""Thanks for telling us about the result for {membership.person.name}. 
        
        When one other person reports the same, we'll mark them as the winner"""

        if not is_elected:
            action_type = ActionType.RETRACT_WINNER
            message = (
                f"Thanks for unsetting{membership.person.name} as the winner"
            )
        if membership.elected:
            message = (
                f"Thanks for confirming {membership.person.name} as the winner"
            )
            action_type = ActionType.SET_CANDIDATE_ELECTED

        change_metadata = get_change_metadata(
            self.request, "Parl 2024 winner form"
        )
        LoggedAction.objects.create(
            user=self.request.user,
            person=membership.person,
            action_type=action_type,
            ip_address=get_client_ip(self.request),
            popit_person_new_version=change_metadata["version_id"],
            source=change_metadata["information_source"],
            edit_type=EditType.USER.name,
        )

        messages.add_message(
            request=self.request,
            level=messages.SUCCESS,
            message=message,
            extra_tags="safe do-something-else",
        )

        return HttpResponseRedirect(reverse("parl_24_winner_form"))
