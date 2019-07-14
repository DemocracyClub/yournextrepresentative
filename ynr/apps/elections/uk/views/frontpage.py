import random

from django.conf import settings
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_control
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import FormView, TemplateView
from django.db.models import F

from candidates.views.mixins import ContributorsMixin
from candidates.models import Ballot

from elections.models import Election

from ..forms import PostcodeForm
from elections.uk.geo_helpers import (
    get_post_elections_from_postcode,
    get_post_elections_from_coords,
)


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

        return context


class PostcodeView(TemplateView):
    template_name = "candidates/postcode_view.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["pees"] = get_post_elections_from_postcode(kwargs["postcode"])
        return context


class GeoLocatorView(TemplateView):
    template_name = "candidates/postcode_view.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        latitude = kwargs["latitude"]
        longitude = kwargs["longitude"]
        coords = ",".join((latitude, longitude))
        context["pees"] = get_post_elections_from_coords(coords)
        # populate the postcode template var with None so the template
        # knows it's a geo-lookup
        context["postcode"] = None
        return context
