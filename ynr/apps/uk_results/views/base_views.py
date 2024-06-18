import contextlib
from datetime import date

from braces.views import LoginRequiredMixin
from candidates.models import Ballot
from django.http import Http404
from django.shortcuts import get_object_or_404
from django.urls import reverse
from django.views.generic import FormView, TemplateView
from uk_results.forms import ResultSetForm


class ResultsHomeView(TemplateView):
    template_name = "uk_results/home.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        elections_list = reverse("election_list_view")
        context[
            "elections_without_results_url"
        ] = f"{elections_list}?has_results=0&is_cancelled=0"
        return context

    def test_func(self, user):
        return True


class BallotPaperResultsUpdateView(LoginRequiredMixin, FormView):
    template_name = "uk_results/ballot_paper_results_form.html"
    form_class = ResultSetForm

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()

        self.ballot = get_object_or_404(
            Ballot,
            cancelled=False,
            voting_system=Ballot.VOTING_SYSTEM_FPTP,
            ballot_paper_id=self.kwargs["ballot_paper_id"],
        )

        if not self.ballot.polls_closed:
            raise Http404(
                f"Polls are still open for {self.ballot.ballot_paper_id}. Please check back after polls close at 10pm."
            )

        with contextlib.suppress(Exception):
            kwargs["instance"] = self.ballot.resultset

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
        return self.ballot.get_absolute_url()


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
                voting_system=Ballot.VOTING_SYSTEM_FPTP,
            )
            .select_related("post", "election")
            .order_by("election__slug", "post__label")
        )

        return context
