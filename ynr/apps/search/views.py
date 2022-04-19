from django.http import HttpResponseRedirect
from django.urls import reverse
from django.views.generic import ListView

from search.utils import search_person_by_name
from search.forms import PersonSearchForm
from elections.uk.lib import is_valid_postcode


class PersonSearch(ListView):
    template_name = "people/search/search.html"
    form_class = PersonSearchForm
    paginate_by = 20

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

    def get_queryset(self):
        return search_person_by_name(
            self.request.GET.get("q", ""), synonym=True
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["query"] = self.request.GET.get("q", "")
        context["looks_like_postcode"] = is_valid_postcode(context["query"])

        return context
