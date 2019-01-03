from django.db.models import Prefetch
from django.views.generic import DetailView, TemplateView
from candidates.models import PostExtraElection
from elections.mixins import ElectionMixin
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


class UnlockedBallotsForElectionListView(ElectionMixin, TemplateView):
    template_name = "elections/unlocked_ballots_for_election_list.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        total_constituencies = 0
        total_locked = 0
        keys = ("locked", "unlocked")
        for k in keys:
            context[k] = []
        postextraelections = (
            PostExtraElection.objects.filter(election=self.election_data)
            .select_related("post")
            .all()
        )
        for postextraelection in postextraelections:
            total_constituencies += 1
            if postextraelection.candidates_locked:
                context_field = "locked"
                total_locked += 1
            else:
                context_field = "unlocked"
            context[context_field].append(
                {
                    "id": postextraelection.post.slug,
                    "name": postextraelection.post.short_label,
                }
            )
        for k in keys:
            context[k].sort(key=lambda c: c["name"])
        context["total_constituencies"] = total_constituencies
        context["total_left"] = total_constituencies - total_locked
        if total_constituencies > 0:
            context["percent_done"] = (
                100 * total_locked
            ) // total_constituencies
        else:
            context["percent_done"] = 0
        return context
