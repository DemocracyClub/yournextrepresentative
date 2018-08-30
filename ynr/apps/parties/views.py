from django.views.generic import TemplateView
from django.shortcuts import get_object_or_404

from popolo.models import Identifier, Membership
from elections.models import Election


class CandidatesByElectionForPartyView(TemplateView):
    template_name = "parties/party_by_election_table.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        party = Identifier.objects.get(
            identifier=kwargs["party_id"]
        ).content_object

        election = None
        try:
            election = Election.objects.get(slug=kwargs["election"])
        except Election.DoesNotExist:
            # This might be a ballot paper ID
            election = get_object_or_404(
                Election, postextraelection__ballot_paper_id=kwargs["election"]
            )

        candidates = (
            Membership.objects.filter(
                post_election__election=election, on_behalf_of=party
            )
            .select_related("post_election", "person")
            .order_by("post_election__post__label")
        )

        context["party"] = party
        context["election"] = election
        context["candidates"] = candidates

        return context
