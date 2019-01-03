from django.db.models import Prefetch
from django.views.generic import DetailView, TemplateView
from candidates.models import PostExtraElection
from elections.models import Election
from popolo.models import Membership


class ElectionView(DetailView):
    template_name = "elections/election_detail.html"
    model = Election
    slug_url_kwarg = "election"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["ballots"] = (
            PostExtraElection.objects.filter(election=self.object)
            .order_by("post__label")
            .select_related("post")
            .select_related("election")
            .select_related("resultset")
            .prefetch_related("suggestedpostlock_set")
            .prefetch_related(
                Prefetch(
                    "membership_set",
                    Membership.objects.select_related("party", "person"),
                )
            )
        )

        return context


class ElectionListView(TemplateView):
    template_name = "elections/election_list.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["elections_and_posts"] = Election.group_and_order_elections(
            include_postextraelections=True, include_noncurrent=False
        )
        return context
