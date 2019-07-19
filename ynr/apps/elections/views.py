from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models import Prefetch, Count
from django.http import JsonResponse, HttpResponseRedirect, HttpResponse
from django.shortcuts import get_object_or_404
from django.utils.decorators import method_decorator
from django.views import View
from django.views.generic import UpdateView
from django.views.decorators.cache import cache_control
from django.views.generic import DetailView, TemplateView
from slugify import slugify

from auth_helpers.views import GroupRequiredMixin
from candidates.csv_helpers import memberships_dicts_for_csv, list_to_csv
from candidates.forms import ToggleLockForm
from candidates.models import (
    Ballot,
    get_edits_allowed,
    TRUSTED_TO_LOCK_GROUP_NAME,
    LoggedAction,
)
from candidates.models.auth import is_post_locked
from candidates.views import get_client_ip
from candidates.views.helpers import (
    get_max_winners,
    get_person_form_fields,
    group_candidates_by_party,
    split_by_elected,
    split_candidacies,
)
from elections.mixins import ElectionMixin
from elections.models import Election
from moderation_queue.forms import SuggestedPostLockForm
from moderation_queue.models import SuggestedPostLock
from official_documents.models import OfficialDocument
from people.forms import NewPersonForm, PersonIdentifierFormsetFactory
from popolo.models import Membership, Post
from parties.models import Party


class ElectionView(DetailView):
    template_name = "elections/election_detail.html"
    model = Election
    slug_url_kwarg = "election"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["ballots"] = (
            Ballot.objects.filter(election=self.object)
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
        from .filters import BallotFilter, filter_shortcuts

        context = super().get_context_data(**kwargs)

        qs = (
            Ballot.objects.filter(election__current=True)
            .select_related("election", "post")
            .prefetch_related("suggestedpostlock_set")
            .prefetch_related("officialdocument_set")
            .annotate(memberships_count=Count("membership"))
            .order_by("election__election_date", "election__name")
        )

        f = BallotFilter(self.request.GET, qs)

        context["filter"] = f
        context["queryset"] = f.qs
        context["shortcuts"] = filter_shortcuts(self.request)

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
        ballots = (
            Ballot.objects.filter(election=self.election_data)
            .select_related("post")
            .all()
        )
        for ballot in ballots:
            total_constituencies += 1
            if ballot.candidates_locked:
                context_field = "locked"
                total_locked += 1
            else:
                context_field = "unlocked"
            context[context_field].append(
                {
                    "id": ballot.post.slug,
                    "name": ballot.post.short_label,
                    "ballot": ballot,
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


class BallotPaperView(TemplateView):
    template_name = "elections/ballot_view.html"

    @method_decorator(cache_control(max_age=(60 * 20)))
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)

    def get_context_data(self, **kwargs):
        from candidates.election_specific import shorten_post_label

        context = super().get_context_data(**kwargs)

        context["ballot"] = ballot = get_object_or_404(
            Ballot.objects.all().select_related("post", "election"),
            ballot_paper_id=context["election"],
        )

        try:
            context["sopn"] = ballot.sopn
        except OfficialDocument.DoesNotExist:
            context["sopn"] = None

        mp_post = context["ballot"].post
        context["election"] = election = context["ballot"].election
        context["post_id"] = post_id = mp_post.slug
        context["post_obj"] = mp_post

        context["post_label"] = mp_post.label
        context["post_label_shorter"] = shorten_post_label(
            context["post_label"]
        )

        context["redirect_after_login"] = context["ballot"].get_absolute_url()

        context["post_data"] = {"id": mp_post.slug, "label": mp_post.label}

        context["candidates_locked"] = ballot.candidates_locked

        context["has_lock_suggestion"] = SuggestedPostLock.objects.filter(
            ballot=ballot
        ).exists()

        if self.request.user.is_authenticated:
            context[
                "current_user_suggested_lock"
            ] = SuggestedPostLock.objects.filter(
                user=self.request.user, ballot=ballot
            ).exists()

        context["suggest_lock_form"] = SuggestedPostLockForm(
            initial={"ballot": ballot}
        )

        if self.request.user.is_authenticated:
            context[
                "user_has_suggested_lock"
            ] = SuggestedPostLock.objects.filter(
                user=self.request.user, ballot=ballot
            ).exists()

        context["lock_form"] = ToggleLockForm(
            initial={
                "post_id": post_id,
                "lock": not context["candidates_locked"],
            }
        )

        context["candidate_list_edits_allowed"] = get_edits_allowed(
            self.request.user, context["candidates_locked"]
        )

        extra_qs = Membership.objects.select_related("ballot__election")
        current_candidacies, past_candidacies = split_candidacies(
            election,
            mp_post.memberships.select_related(
                "person", "party", "ballot__election"
            ).all(),
        )

        current_candidates = {c.person for c in current_candidacies}
        past_candidates = {c.person for c in past_candidacies}

        other_candidates = past_candidates - current_candidates

        elected, unelected = split_by_elected(election, current_candidacies)

        # Now split those candidates into those that we know aren't
        # standing again, and those that we just don't know about.
        not_standing_candidates = {
            p for p in other_candidates if election in p.not_standing.all()
        }
        might_stand_candidates = {
            p for p in other_candidates if election not in p.not_standing.all()
        }
        might_stand_candidates = {
            p for p in might_stand_candidates if p.death_date == ""
        }

        not_standing_candidacies = [
            c for c in past_candidacies if c.person in not_standing_candidates
        ]
        might_stand_candidacies = [
            c for c in past_candidacies if c.person in might_stand_candidates
        ]

        context["candidacies_not_standing_again"] = group_candidates_by_party(
            election, not_standing_candidacies
        )

        context["candidacies_might_stand_again"] = group_candidates_by_party(
            election, might_stand_candidacies
        )

        context["elected"] = group_candidates_by_party(
            election, elected, show_all=True
        )
        context["unelected"] = group_candidates_by_party(election, unelected)

        context["show_retract_result"] = False
        number_of_winners = 0
        for c in current_candidacies:
            if c.elected:
                number_of_winners += 1
            if c.elected is not None:
                context["show_retract_result"] = True

        max_winners = get_max_winners(ballot)
        context["show_confirm_result"] = bool(max_winners)
        if not ballot.candidates_locked:
            context["add_candidate_form"] = NewPersonForm(
                election=election.slug,
                initial={
                    ("constituency_" + election.slug): post_id,
                    ("standing_" + election.slug): "standing",
                },
                hidden_post_widget=True,
            )

            context = get_person_form_fields(
                context, context["add_candidate_form"]
            )
            context["identifiers_formset"] = PersonIdentifierFormsetFactory()

        return context


class LockBallotView(GroupRequiredMixin, UpdateView):
    required_group_name = TRUSTED_TO_LOCK_GROUP_NAME

    http_method_names = ["post"]
    model = Ballot
    slug_url_kwarg = "ballot_id"
    slug_field = "ballot_paper_id"
    form_class = ToggleLockForm

    def form_valid(self, form):
        with transaction.atomic():
            ballot = form.instance

            self.object = form.save()
            if hasattr(ballot, "rawpeople"):
                # Delete the raw import, as it's no longer useful
                self.object.rawpeople.delete()

            lock = self.object.candidates_locked
            post_name = ballot.post.short_label
            if lock:
                suffix = "-lock"
                pp = "Locked"
                # If we're locking this, then the suggested posts
                # can be deleted
                ballot.suggestedpostlock_set.all().delete()
            else:
                suffix = "-unlock"
                pp = "Unlocked"
            message = pp + " ballot {} ({})".format(
                post_name, ballot.ballot_paper_id
            )

            LoggedAction.objects.create(
                user=self.request.user,
                action_type="constituency-{}".format(suffix),
                ip_address=get_client_ip(self.request),
                ballot=ballot,
                source=message,
            )
        if self.request.is_ajax():
            return JsonResponse({"locked": ballot.candidates_locked})
        else:
            return HttpResponseRedirect(ballot.get_absolute_url())


class BallotPaperCSVView(DetailView):
    queryset = Ballot.objects.select_related("election", "post")
    slug_url_kwarg = "ballot_id"
    slug_field = "ballot_paper_id"

    def get(self, request, *args, **kwargs):
        ballot = self.get_object()
        memberships_dict, elected = memberships_dicts_for_csv(
            election_slug=ballot.election.slug, post_slug=ballot.post.slug
        )

        filename = "{ballot_paper_id}.csv".format(
            ballot_paper_id=ballot.ballot_paper_id
        )
        response = HttpResponse(content_type="text/csv")
        response["Content-Disposition"] = 'attachment; filename="%s"' % filename
        response.write(list_to_csv(memberships_dict[ballot.election.slug]))
        return response


class SOPNForBallotView(DetailView):
    """
    A view to show a single SOPN for a ballot paper
    """

    model = Ballot
    slug_url_kwarg = "ballot_id"
    slug_field = "ballot_paper_id"
    template_name = "elections/sopn_for_ballot.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["documents_with_same_source"] = OfficialDocument.objects.filter(
            source_url=self.object.sopn.source_url
        )

        return context


class PartyForBallotView(DetailView):
    model = Ballot
    slug_url_kwarg = "ballot_id"
    slug_field = "ballot_paper_id"
    template_name = "elections/party_for_ballot.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["party"] = get_object_or_404(
            Party, ec_id=self.kwargs["party_id"]
        )
        context["candidates"] = self.object.membership_set.filter(
            party=context["party"]
        ).order_by("party_list_position")
        return context
