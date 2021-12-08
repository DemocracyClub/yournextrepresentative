from django.shortcuts import get_object_or_404

from candidates.models import Ballot
from .models import Election


class ElectionMixin(object):
    """A mixin to add election data from the URL to the context"""

    def get_ballot(self):
        ballot_paper_id = self.kwargs["ballot_paper_id"]
        ballot_qs = Ballot.objects.all().select_related("post", "election")
        return get_object_or_404(ballot_qs, ballot_paper_id=ballot_paper_id)

    def get_election(self):
        election = self.kwargs.get("election")
        return get_object_or_404(Election, slug=election)

    def dispatch(self, request, *args, **kwargs):
        if self.kwargs.get("ballot_paper_id"):
            self.ballot = self.get_ballot()
            self.election_data = self.ballot.election
            self.election = self.ballot.election.slug
        else:
            self.election = self.kwargs["election"]
            self.election_data = self.get_election()
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["election"] = self.election
        context["election_data"] = self.election_data
        if self.kwargs.get("ballot_paper_id"):
            context["ballot"] = self.ballot
        return context
