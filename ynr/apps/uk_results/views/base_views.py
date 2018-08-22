from datetime import date

from braces.views import LoginRequiredMixin
from django.views.generic import FormView, TemplateView

from candidates.models import PostExtraElection
from uk_results.forms import ResultSetForm


class ResultsHomeView(TemplateView):
    template_name = "uk_results/home.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        return context

    def test_func(self, user):
        return True


class BallotPaperResultsUpdateView(LoginRequiredMixin, FormView):
    template_name = "uk_results/ballot_paper_results_form.html"
    form_class = ResultSetForm

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        self.pee = PostExtraElection.objects.get(
            ballot_paper_id=self.kwargs["ballot_paper_id"]
        )
        try:
            kwargs["instance"] = self.pee.resultset
        except:
            pass
        kwargs["post_election"] = self.pee
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context["post_election"] = self.pee
        context["resultset"] = getattr(self.pee, "resultset", None)
        return context

    def form_valid(self, form):
        self.resultset = form.save(self.request)
        return super().form_valid(form)

    def get_success_url(self):
        url = self.pee.get_absolute_url()
        return url


class CurrentElectionsWithNoResuts(TemplateView):
    template_name = "uk_results/current_elections_with_no_resuts.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context["elections"] = (
            PostExtraElection.objects.filter(
                election__current=True,
                election__election_date__lt=date.today(),
                resultset=None,
            )
            .select_related("postextra__base", "election")
            .order_by("election", "postextra__base__label")
        )

        return context
