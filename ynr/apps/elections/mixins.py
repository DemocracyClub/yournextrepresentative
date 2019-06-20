from django.shortcuts import get_object_or_404

from .models import Election


class ElectionMixin(object):
    """A mixin to add election data from the URL to the context"""

    def get_election(self):
        election = self.kwargs["election"]
        return get_object_or_404(Election, slug=election)

    def dispatch(self, request, *args, **kwargs):
        self.election = election = self.kwargs["election"]
        self.election_data = self.get_election()
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["election"] = self.election
        context["election_data"] = self.election_data
        return context
