import json

from django.views.generic import TemplateView, View
from django.http import HttpResponse
from django.db.models import Count

from elections.models import Election



class ResultsHomeView(TemplateView):
    template_name = "uk_results/home.html"

    def get_context_data(self, **kwargs):
        context = super(ResultsHomeView, self).get_context_data(**kwargs)


        return context

    def test_func(self, user):
        return True

