from collections.__init__ import defaultdict

from django.views.generic import TemplateView
from django.shortcuts import get_object_or_404

from elections.mixins import ElectionMixin

from candidates.models import Ballot
from popolo.models import Identifier, Membership
from elections.models import Election

from .models import Party


def get_post_group_stats(posts):
    total = 0
    candidates = 0
    proportion = 0
    for post, members in posts.items():
        total += 1
        candidates += len(members)
    if total > 0:
        proportion = candidates / float(total)
    return {
        "proportion": proportion,
        "total": total,
        "candidates": candidates,
        "missing": total - candidates,
        "show_all": proportion > 0.3,
    }


class CandidatesByElectionForPartyView(TemplateView):
    template_name = "parties/party_by_election_table.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        party = Party.objects.get(ec_id=kwargs["party_id"])

        candidates_qs = party.membership_set.select_related(
            "post_election", "person", "post_election__post"
        )

        try:
            election = Election.objects.get(slug=kwargs["election"])
            candidates_qs = candidates_qs.filter(
                post_election__election=election
            )
            ballot = None

        except Election.DoesNotExist:
            # This might be a ballot paper ID
            ballot = get_object_or_404(
                Ballot, ballot_paper_id=kwargs["election"]
            )
            election = ballot.election
            candidates_qs = candidates_qs.filter(
                post_election__ballot_paper_id=ballot
            )

        candidates_qs = candidates_qs.order_by("post_election__post__label")

        context["party"] = party
        context["election"] = election
        context["ballot"] = ballot
        context["candidates"] = candidates_qs

        return context
