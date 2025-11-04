from typing import Tuple, Type

from candidates.models import Ballot
from data_exports.models import MaterializedMemberships
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Count, F
from django.http import Http404
from django.views.generic import DetailView, ListView, TemplateView
from elections.mixins import ElectionMixin
from parties.models import Party
from ynr_refactoring.settings import PersonIdentifierFields

from .filters import CompletenessFilter
from .models import ElectionReport, get_attention_needed_posts
from .report_helpers import (
    BallotsContestedPerParty,
    BaseReport,
    CandidatesPerParty,
    CommonFirstNames,
    CommonLastNames,
    MostPerSeat,
    NcandidatesPerSeat,
    NewParties,
    NumberOfBallots,
    NumberOfCandidates,
    NumberOfSeats,
    NumCandidatesStandingInMultipleSeats,
    PartyMovers,
    TwoWayRace,
    TwoWayRaceForNcandidates,
    TwoWayRaceForNewParties,
    UncontestedBallots,
)


class ReportsHomeView(ListView):
    template_name = "reports.html"
    paginate_by = 20

    def get_queryset(self, **kwargs):
        return (
            MaterializedMemberships.objects.all()
            .values(
                "election_date", "election_name", "ballot_paper__election__slug"
            )
            .annotate(candidates=Count("person_id"))
        )


class PartyCountsView(ElectionMixin, TemplateView):
    template_name = "party_counts.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        qs = Party.objects.filter(
            membership__ballot__election=self.election_data
        )
        qs = qs.annotate(count=Count("membership"))
        qs = qs.order_by("-count", "name")

        context["party_counts"] = qs

        return context


class ConstituencyCountsView(ElectionMixin, TemplateView):
    template_name = "constituency_counts.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        qs = Ballot.objects.filter(election=self.election_data).annotate(
            count=Count("membership")
        )
        qs = qs.select_related("post", "election")
        qs = qs.order_by("-count")

        context["post_counts"] = qs
        return context


class AttentionNeededView(TemplateView):
    template_name = "attention_needed.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["post_counts"] = get_attention_needed_posts()
        return context


DEFAULT_REPORTS: Tuple[Type[BaseReport]] = (
    NumberOfCandidates,
    NumberOfBallots,
    NumberOfSeats,
    CandidatesPerParty,
    BallotsContestedPerParty,
    UncontestedBallots,
    NcandidatesPerSeat,
    TwoWayRace,
    TwoWayRaceForNewParties,
    TwoWayRaceForNcandidates,
    MostPerSeat,
    NewParties,
    PartyMovers,
    NumCandidatesStandingInMultipleSeats,
    CommonFirstNames,
    CommonLastNames,
)


class ElectionReportView(DetailView):
    model = ElectionReport

    def get_object(self, queryset=None):
        election_type, election_date = self.kwargs["report_slug"].split("-", 1)
        qs = self.model.objects.filter(
            election_type=election_type,
            election_date=election_date,
        )
        try:
            return qs.get()
        except self.model.DoesNotExist:
            raise Http404("Report not found")

    template_name = "cached_counts/election-report.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context["reports"] = {}

        for report_klass in DEFAULT_REPORTS:
            report = report_klass(
                str(self.object.election_date),
                election_type=self.object.election_type,
            )
            report.run()
            context["reports"][report.__class__.__name__] = report

        return context


class CandidateCompletenessView(
    LoginRequiredMixin, ElectionMixin, TemplateView
):
    template_name = "candidate_completeness.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        qs = MaterializedMemberships.objects.filter(
            ballot_paper__election__slug=self.election
        )

        identifier_fields = sorted(pi.name for pi in PersonIdentifierFields)
        annotations = {}
        for field in identifier_fields:
            annotations[field] = F(f"identifiers__{field}")
        qs = qs.annotate(**annotations)

        filter_set = CompletenessFilter(self.request.GET, queryset=qs)
        context["filter_set"] = filter_set
        context["qs"] = filter_set.qs
        context["percentages"] = filter_set.qs.percentage_for_fields()
        context["identifier_fields"] = identifier_fields

        return context
