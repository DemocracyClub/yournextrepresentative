from collections.__init__ import defaultdict

from django.views.generic import TemplateView
from django.shortcuts import get_object_or_404

from candidates.models import OrganizationExtra
from elections.mixins import ElectionMixin

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
        election = None
        try:
            election = Election.objects.get(slug=kwargs["election"])
        except Election.DoesNotExist:
            # This might be a ballot paper ID
            election = get_object_or_404(
                Election, postextraelection__ballot_paper_id=kwargs["election"]
            )

        candidates = party.membership_set.select_related(
            "post_election", "person"
        ).order_by("post_election__post__label")

        context["party"] = party
        context["election"] = election
        context["candidates"] = candidates

        return context


class PartyListView(ElectionMixin, TemplateView):
    template_name = "candidates/party-list.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["parties"] = Party.objects.filter(
            membership__post_election__election=self.election_data
        ).distinct()
        return context


class PartyDetailView(ElectionMixin, TemplateView):
    template_name = "candidates/party.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        party_id = kwargs["legacy_slug"]
        party = get_object_or_404(Party, legacy_slug=party_id)

        # Make the party emblems conveniently available in the context too:
        context["emblems"] = party.emblems.all()
        all_post_groups = self.election_data.posts.values_list(
            "group", flat=True
        ).distinct()
        by_post_group = {
            pg: {"stats": None, "posts_with_memberships": defaultdict(list)}
            for pg in all_post_groups
        }
        for membership in (
            Membership.objects.filter(
                party=party,
                post_election__election=self.election_data,
                role=self.election_data.candidate_membership_role,
            )
            .select_related()
            .prefetch_related("post", "person")
        ):
            person = membership.person
            post = membership.post
            post_group = post.group
            by_post_group[post_group]["posts_with_memberships"][post].append(
                {"membership": membership, "person": person, "post": post}
            )
        # That'll only find the posts that someone from the party is
        # actually standing for, so add any other posts...
        for post in self.election_data.posts.all():
            post_group = post.group
            post_group_data = by_post_group[post_group]
            posts_with_memberships = post_group_data["posts_with_memberships"]
            posts_with_memberships.setdefault(post, [])
        context["party"] = party
        context["party_name"] = party.name
        for post_group, data in by_post_group.items():
            posts_with_memberships = data["posts_with_memberships"]
            by_post_group[post_group]["stats"] = get_post_group_stats(
                posts_with_memberships
            )
            data["posts_with_memberships"] = sorted(
                posts_with_memberships.items(), key=lambda t: t[0].label
            )
        context["candidates_by_post_group"] = sorted(
            [
                (pg, data)
                for pg, data in by_post_group.items()
                if pg in all_post_groups
            ],
            key=lambda k: k[0],
        )
        return context
