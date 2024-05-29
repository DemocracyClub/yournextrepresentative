import json
from typing import Tuple, Type

from candidates.models import Ballot
from data_exports.models import MaterializedMemberships
from django.db.models import Count, F
from django.http import Http404, HttpResponse
from django.views.generic import DetailView, TemplateView
from elections.mixins import ElectionMixin
from elections.models import Election
from parties.models import Party
from popolo.models import Membership
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


def get_counts(for_json=True):
    election_id_to_candidates = {}
    qs = (
        Membership.objects.all()
        .values("ballot__election")
        .annotate(count=Count("ballot__election"))
        .order_by()
    )

    for d in qs:
        election_id_to_candidates[d["ballot__election"]] = d["count"]

    grouped_elections = Election.group_and_order_elections(for_json=for_json)
    for era_data in grouped_elections:
        for date, elections in era_data["dates"].items():
            for role_data in elections:
                for election_data in role_data["elections"]:
                    e = election_data["election"]
                    total = election_id_to_candidates.get(e.id, 0)
                    election_counts = {
                        "id": e.slug,
                        "html_id": e.slug.replace(".", "-"),
                        "name": e.name,
                        "total": total,
                    }
                    election_data.update(election_counts)
                    del election_data["election"]
    return grouped_elections


class ReportsHomeView(TemplateView):
    template_name = "reports.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["all_elections"] = get_counts()
        return context

    def get(self, *args, **kwargs):
        if self.request.GET.get("format") == "json":
            return HttpResponse(
                json.dumps(get_counts(for_json=True)),
                content_type="application/json",
            )
        return super().get(*args, **kwargs)


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


class CandidateCompletenessView(ElectionMixin, TemplateView):
    template_name = "candidate_completeness.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        qs = MaterializedMemberships.objects.filter(
            ballot_paper__election__slug=self.election
        ).select_related("person", "ballot_paper")

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
