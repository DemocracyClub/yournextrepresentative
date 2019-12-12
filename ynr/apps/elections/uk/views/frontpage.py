import datetime
from urllib.parse import urlencode

from django.conf import settings
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_control
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import FormView, TemplateView
from django_filters import FilterSet, filters

from candidates.views.mixins import ContributorsMixin
from elections.uk.geo_helpers import (
    get_ballots_from_coords,
    get_ballots_from_postcode,
)

from ..forms import PostcodeForm


class HomePageView(ContributorsMixin, FormView):
    template_name = "candidates/finder.html"
    form_class = PostcodeForm

    @method_decorator(cache_control(max_age=(60 * 10)))
    @method_decorator(csrf_exempt)
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)

    def get_form_kwargs(self):
        if self.request.method == "GET" and "q" in self.request.GET:
            return {
                "data": self.request.GET,
                "initial": self.get_initial(),
                "prefix": self.get_prefix(),
            }
        else:
            return super().get_form_kwargs()

    def get(self, request, *args, **kwargs):
        if "q" in request.GET:
            # The treat it like a POST request; we've overridden
            # get_form_kwargs to make sure the GET parameters are used
            # for the form in this case.
            return self.post(request, *args, **kwargs)
        else:
            return super().get(request, *args, **kwargs)

    def form_valid(self, form):
        postcode = form.cleaned_data["q"]
        return HttpResponseRedirect(
            reverse("postcode-view", kwargs={"postcode": postcode})
        )

    def ge_2019_results_context(self):
        context = {}
        polls_close = timezone.make_aware(
            datetime.datetime.strptime("2019-12-12 22", "%Y-%m-%d %H")
        )
        now = timezone.now()

        context["polls_closed"] = polls_close < now

        from candidates.models import Ballot

        class ResultsFilter(FilterSet):
            class Meta:
                model = Ballot
                fields = ["winner", "votes_cast"]

            winner = filters.BooleanFilter(
                field_name="membership__elected", lookup_expr="isnull"
            )
            votes_cast = filters.BooleanFilter(
                field_name="resultset", lookup_expr="isnull"
            )

        def filter_shortcuts(request):
            shortcut_list = [
                {
                    "name": "winners_set",
                    "label": "Elected",
                    "query": {"winner": ["False"]},
                },
                {
                    "name": "winners_not_set",
                    "label": "No elected result",
                    "query": {"winner": ["True"]},
                },
                {
                    "name": "votes_cast",
                    "label": "No votes result",
                    "query": {"votes_cast": ["True"]},
                },
                {
                    "name": "votes_cast",
                    "label": "Votes result",
                    "query": {"votes_cast": ["False"]},
                },
            ]

            query = dict(request.GET)
            shortcuts = {"list": shortcut_list}
            for shortcut in shortcuts["list"]:
                shortcut["querystring"] = urlencode(
                    shortcut["query"], doseq=True
                )
                if shortcut["query"] == query:
                    shortcut["active"] = True
                    shortcuts["active"] = shortcut
            return shortcuts

        from popolo.models import Membership

        election_slug = "parl.2017-06-08"

        ballots_qs = (
            Ballot.objects.filter(election__slug=election_slug)
            .select_related("post", "resultset")
            .order_by("ballot_paper_id")
        ).distinct("ballot_paper_id")
        f = ResultsFilter(self.request.GET, ballots_qs)

        winners = Membership.objects.filter(
            ballot__in=f.qs, elected=True
        ).select_related("ballot", "person", "party")

        context["winners_dict"] = {}
        for winner in winners:
            context["winners_dict"][winner.ballot.ballot_paper_id] = winner

        for ballot in f.qs:
            if ballot.ballot_paper_id in context["winners_dict"]:
                ballot.winner = context["winners_dict"][ballot.ballot_paper_id]

        context["shortcuts"] = filter_shortcuts(self.request)
        context["ballots_with_result_info"] = f

        return context

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["front_page_cta"] = getattr(settings, "FRONT_PAGE_CTA", None)
        context["postcode_form"] = kwargs.get("form") or PostcodeForm()
        context["show_postcode_form"] = True
        context["show_name_form"] = False
        context["top_users"] = self.get_leaderboards(all_time=False)[0]["rows"][
            :8
        ]
        context["recent_actions"] = self.get_recent_changes_queryset()[:5]

        context["ge_2019_results"] = self.ge_2019_results_context()
        return context


class PostcodeView(TemplateView):
    template_name = "candidates/postcode_view.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["ballots"] = get_ballots_from_postcode(kwargs["postcode"])
        return context


class GeoLocatorView(TemplateView):
    template_name = "candidates/postcode_view.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        latitude = kwargs["latitude"]
        longitude = kwargs["longitude"]
        coords = ",".join((latitude, longitude))
        context["ballots"] = get_ballots_from_coords(coords)
        # populate the postcode template var with None so the template
        # knows it's a geo-lookup
        context["postcode"] = None
        return context
