from datetime import date

from braces.views import LoginRequiredMixin
from django.views.generic import FormView, TemplateView

from candidates.models import Ballot
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
        self.ballot = Ballot.objects.get(
            ballot_paper_id=self.kwargs["ballot_paper_id"],
            # if we try to add results to a cancelled election, throw a 404
            cancelled=False,
        )
        try:
            kwargs["instance"] = self.ballot.resultset
        except:
            pass
        kwargs["ballot"] = self.ballot
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context["ballot"] = self.ballot
        context["resultset"] = getattr(self.ballot, "resultset", None)
        return context

    def form_valid(self, form):
        self.resultset = form.save(self.request)
        return super().form_valid(form)

    def get_success_url(self):
        url = self.ballot.get_absolute_url()
        return url


class CurrentElectionsWithNoResuts(TemplateView):
    template_name = "uk_results/current_elections_with_no_resuts.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context["elections"] = (
            Ballot.objects.filter(
                election__current=True,
                election__election_date__lte=date.today(),
                resultset=None,
                cancelled=False,
            )
            .select_related("post", "election")
            .order_by("election__slug", "post__label")
        )

        return context
