import operator
from functools import reduce

from django.contrib.postgres.search import SearchQuery, SearchVector, SearchRank
from django.db.models import Count
from django.forms import forms
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.utils.html import escape
from django.views.generic import TemplateView
from slacker2 import Search

from elections.uk.lib import is_valid_postcode
from people.models import Person
from popolo.models import Membership


def or_term(term):
    terms = [SearchQuery(term_sq) for term_sq in term.split(" ")]
    if len(terms) == 1:
        return terms[0]
    return reduce(operator.or_, terms)


def search_person_by_name(name):
    vector = SearchVector("name")
    query = or_term(name)

    qs = (
        Person.objects
        # .values("person_id")
        .annotate(membership_count=Count("memberships"))
        .filter(name__search=query)
        .annotate(rank=SearchRank(vector, query))
        .order_by("-rank", "-membership_count")
        .defer("biography", "versions")
    )

    return qs


class PersonSearchForm(forms.Form):
    def clean_q(self):
        return escape(self.cleaned_data["q"])

    def search(self):
        return search_person_by_name(self.cleaned_data["q"])[:10]


class PersonSearch(TemplateView):
    template_name = "people/search/search.html"
    form_class = PersonSearchForm

    def get(self, request, *args, **kwargs):
        ret = super().get(request, *args, **kwargs)
        context = ret.context_data

        if context["looks_like_postcode"]:
            if not context.get("results"):
                # This looks like a postcode, and we've found nothing else
                # so redirect to a postcode view.
                home_page = reverse("lookup-postcode")
                return HttpResponseRedirect(
                    "{}?q={}".format(home_page, context["query"])
                )

        return ret

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["query"] = self.request.GET.get("q")
        context["looks_like_postcode"] = is_valid_postcode(context["query"])
        if context["query"]:
            context["results"] = search_person_by_name(context["query"])[:10]

        return context
