from django.views.generic import TemplateView


class ResultsHomeView(TemplateView):
    template_name = "uk_results/home.html"

    def get_context_data(self, **kwargs):
        context = super(ResultsHomeView, self).get_context_data(**kwargs)


        return context

    def test_func(self, user):
        return True
