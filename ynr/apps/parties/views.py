from django.views.generic import TemplateView
from django.shortcuts import get_object_or_404

from popolo.models import Identifier
from candidates.models import MembershipExtra
from elections.models import Election


class CandidatesByElectionForPartyView(TemplateView):
    template_name = "parties/party_by_election_table.html"
    def get_context_data(self, **kwargs):
        context = super(
            CandidatesByElectionForPartyView, self).get_context_data(**kwargs)

        party = Identifier.objects.get(
            identifier=kwargs['party_id']).content_object

        election = None
        try:
            election = Election.objects.get(slug=kwargs['election'])
        except Election.DoesNotExist:
            # This might be a ballot paper ID
            election = get_object_or_404(
                Election,
                postextraelection__ballot_paper_id=kwargs['election']
            )


        candidates = MembershipExtra.objects.filter(
            post_election__election=election,
            base__on_behalf_of=party
        ).select_related(
            'post_election',
            'base',
            'base__person',
            'base__person__extra',
        ).order_by('post_election__postextra__base__label')

        context['party'] = party
        context['election'] = election
        context['candidates'] = candidates


        return context

