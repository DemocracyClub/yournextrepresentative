import csv
from datetime import date
import os

from braces.views import LoginRequiredMixin
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django.views.generic import FormView, TemplateView

from candidates.models import Ballot
from popolo.models import Membership
from results.models import ResultEvent
from uk_results.forms import ResultSetForm
from ynr.apps import resultsbot


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

        self.ballot = get_object_or_404(
            Ballot,
            cancelled=False,
            voting_system=Ballot.VOTING_SYSTEM_FPTP,
            ballot_paper_id=self.kwargs["ballot_paper_id"],
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
                voting_system=Ballot.VOTING_SYSTEM_FPTP,
            )
            .select_related("post", "election")
            .order_by("election__slug", "post__label")
        )

        return context

    def get_ballot_paper_ids_from_csv(self):
        path = os.path.join(
            os.path.dirname(resultsbot.__file__), "election_id_to_url.csv"
        )
        with open(path) as f:
            csv_file = csv.reader(f)
            ballot_paper_ids = []
            for row in csv_file:
                try:
                    ballot_paper_ids.append(row[0])
                except IndexError:
                    continue
            return ballot_paper_ids

    def results_by_bot(self):
        elections = self.context["elections"]
        ballot_paper_ids = self.get_ballot_paper_ids_from_csv()
        for election in elections:
            if election.ballot_paper_id in ballot_paper_ids:
                return True
            else:
                return False


class Parl19ResultsCSVView(TemplateView):
    """
    A view just for exporting the winners of the GE2019 election.

    Not generalized at all, because it's tricky. Designed to make it easy
    to move the URL / namespace about later, without breaking things for
    other possible CSVs
    """

    def get(self, *args, **kwargs):
        qs = (
            Membership.objects.filter(
                elected=True, ballot__election__slug="parl.2019-12-12"
            )
            .select_related(
                "ballot", "ballot__election", "ballot__post", "person", "party"
            )
            .prefetch_related("person__tmp_person_identifiers")
        )

        response = HttpResponse(content_type="text/html")
        response[
            "Content-Disposition"
        ] = 'attachment; filename="parl-2019-12-12_winners.csv"'

        fieldnames = [
            "election_slug",
            "ballot_paper_id",
            "gss",
            "person_id",
            "person_name",
            "party_id",
            "party_name",
            "theyworkforyou_url",
            "wikidata_id",
            "updated",
            "previous_winner",
            "previous_winner_party",
        ]
        writer = csv.DictWriter(response, fieldnames=fieldnames)
        writer.writeheader()
        for membership in qs:
            twfy_id = membership.person.get_single_identifier_of_type(
                "theyworkforyou"
            )
            theyworkforyou_url = None
            if twfy_id:
                theyworkforyou_url = "http://www.theyworkforyou.com/mp/{}".format(
                    twfy_id.internal_identifier
                )

            result = ResultEvent.objects.filter(
                election=membership.ballot.election,
                post=membership.ballot.post,
                winner=membership.person,
            )
            if result.exists():
                created = result.first().created
            else:
                created = None

            previous_ballot = Ballot.objects.get_previous_ballot_for_post(
                membership.ballot
            )
            previous_winner_qs = previous_ballot.membership_set.filter(
                elected=True
            )
            if previous_winner_qs.exists():
                previous_winner = previous_winner_qs.first()
            else:
                previous_winner = None

            gss = None
            if membership.ballot.post.identifier.startswith("gss:"):
                gss = membership.ballot.post.identifier[4:]

            out = {
                "election_slug": membership.ballot.election.slug,
                "ballot_paper_id": membership.ballot.ballot_paper_id,
                "gss": gss,
                "person_id": membership.person_id,
                "person_name": membership.person.name,
                "party_id": membership.party.ec_id,
                "party_name": membership.party.name,
                "theyworkforyou_url": theyworkforyou_url,
                "wikidata_id": membership.person.get_single_identifier_of_type(
                    "wikidata_id"
                ).value,
                "updated": created,
            }
            if previous_winner:
                out.update(
                    {
                        "previous_winner": previous_winner.person_id,
                        "previous_winner_party": previous_winner.party.ec_id,
                    }
                )
            writer.writerow(out)

        return response
