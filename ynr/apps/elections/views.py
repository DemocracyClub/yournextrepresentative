from auth_helpers.views import GroupRequiredMixin
from candidates.csv_helpers import list_to_csv, memberships_dicts_for_csv
from candidates.forms import ToggleLockForm
from candidates.models import (
    TRUSTED_TO_LOCK_GROUP_NAME,
    Ballot,
    LoggedAction,
    PartySet,
)
from candidates.models.db import ActionType
from candidates.views.version_data import get_client_ip
from django.contrib import messages
from django.db import transaction
from django.db.models import Count, Q
from django.db.models.functions import Coalesce
from django.http import HttpResponse, HttpResponseRedirect, JsonResponse
from django.shortcuts import get_object_or_404
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.cache import cache_control, cache_page
from django.views.generic import DetailView, TemplateView, UpdateView
from elections.mixins import ElectionMixin
from elections.models import Election
from moderation_queue.forms import SuggestedPostLockForm
from official_documents.models import BallotSOPN
from parties.models import Party
from people.forms.forms import NewPersonForm
from people.forms.formsets import PersonIdentifierFormsetFactory
from popolo.models import Membership
from utils.db import LastWord, NullIfBlank


class ElectionView(DetailView):
    template_name = "elections/election_detail.html"
    model = Election
    slug_url_kwarg = "election"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context["memberships"] = (
            Membership.objects.filter(ballot__election=self.object)
            .select_related(
                "ballot",
                "ballot__post",
                "ballot__resultset",
                "person",
                "party",
                "result",
            )
            .annotate(last_name=LastWord("person__name"))
            .annotate(
                name_for_ordering=Coalesce(
                    NullIfBlank("person__sort_name"), "last_name"
                )
            )
            .order_by(
                "ballot__post__label",
                "-elected",
                "-result__num_ballots",
                "name_for_ordering",
            )
        )

        return context


class ElectionListView(TemplateView):
    template_name = "elections/election_list.html"

    def get_context_data(self, **kwargs):
        from .filters import CurrentOrFutureBallotFilter, filter_shortcuts

        context = super().get_context_data(**kwargs)
        qs = (
            Ballot.objects.current_or_future()
            .select_related("election", "post")
            .select_related("resultset")
            .prefetch_related("suggestedpostlock_set")
            .prefetch_related("officialdocument_set")
            .annotate(memberships_count=Count("membership", distinct=True))
            .annotate(
                elected_count=Count(
                    "membership",
                    distinct=True,
                    filter=Q(membership__elected=True),
                )
            )
            .order_by(
                "election__election_date", "election__name", "post__label"
            )
        )
        f = CurrentOrFutureBallotFilter(self.request.GET, qs)

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

    def get_authenticated_user_context(self, ballot, context):
        """
        Stuff we only want to add if the user is authenticated
        """

        # Lock Suggestions
        if ballot.has_lock_suggestion:
            context[
                "current_user_suggested_lock"
            ] = ballot.suggestedpostlock_set.filter(
                user=self.request.user
            ).exists()
        else:
            context["suggest_lock_form"] = SuggestedPostLockForm(
                initial={"ballot": ballot}
            )

        # Check if adding and removing Memberships for this ballot
        # is allowed.
        context["membership_edits_allowed"] = ballot.user_can_edit_membership(
            self.request.user, allow_if_trusted_to_lock=True
        )

        if context["membership_edits_allowed"]:
            # New person form
            context["add_candidate_form"] = NewPersonForm(
                initial={"ballot_paper_id": ballot.ballot_paper_id}
            )
            context["identifiers_formset"] = PersonIdentifierFormsetFactory()

            # Previous candidate suggestions
            context["previous_ballot"] = (
                previous_ballot
            ) = Ballot.objects.get_previous_ballot_for_post(ballot)
            if previous_ballot and not ballot.polls_closed:
                context[
                    "people_not_standing"
                ] = ballot.people_not_standing_again(previous_ballot)

                context[
                    "candidates_might_stand_again"
                ] = Membership.objects.memberships_for_ballot(
                    previous_ballot,
                    exclude_memberships_qs=context["candidates"],
                    exclude_people_qs=context["people_not_standing"],
                )

        return context

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context["ballot"] = ballot = get_object_or_404(
            Ballot.objects.all().select_related(
                "post", "election", "resultset"
            ),
            ballot_paper_id=context["election"],
        )

        context["candidates"] = Membership.objects.memberships_for_ballot(
            ballot
        )

        try:
            context["sopn"] = ballot.sopn
        except BallotSOPN.DoesNotExist:
            context["sopn"] = None

        if ballot.polls_closed:
            winners = [m.elected for m in context["candidates"]]
            context["has_any_winners"] = any(winners)
            context["has_all_winners"] = (
                winners.count(True) == ballot.winner_count
            )

        if self.request.user.is_authenticated:
            context = self.get_authenticated_user_context(ballot, context)

        return context


class LockBallotView(GroupRequiredMixin, UpdateView):
    required_group_name = TRUSTED_TO_LOCK_GROUP_NAME

    http_method_names = ["post"]
    model = Ballot
    slug_url_kwarg = "ballot_id"
    slug_field = "ballot_paper_id"
    form_class = ToggleLockForm

    def form_invalid(self, form):
        if self.request.headers.get("x-requested-with") == "XMLHttpRequest":
            return JsonResponse(data={"ballot_updated": True})

        messages.error(
            request=self.request,
            message="Locking failed as it looks like the ballot was changed by another user since loading. Please review any new changes before attempting to lock again.",
            extra_tags="safe ballot-changed",
        )
        return HttpResponseRedirect(self.object.get_absolute_url())

    def form_valid(self, form):
        with transaction.atomic():
            ballot = form.instance

            self.object = form.save()
            if hasattr(ballot, "rawpeople"):
                # Delete the raw import, as it's no longer useful
                self.object.rawpeople.delete()

            lock = self.object.candidates_locked
            post_name = ballot.post.short_label
            request = self.request
            ip_address = get_client_ip(request)
            if lock:
                action_type = ActionType.CONSTITUENCY_LOCK
                pp = "Locked"
                # If we're locking this, then the suggested posts
                # can be deleted
                ballot.suggestedpostlock_set.all().delete()
                ballot.mark_uncontested_winners(
                    ip_address=ip_address, user=request.user
                )
            else:
                action_type = ActionType.CONSTITUENCY_UNLOCK
                pp = "Unlocked"
                ballot.unmark_uncontested_winners(
                    ip_address=ip_address, user=request.user
                )
            message = pp + " ballot {} ({})".format(
                post_name, ballot.ballot_paper_id
            )
            LoggedAction.objects.create(
                user=self.request.user,
                action_type=action_type,
                ip_address=get_client_ip(self.request),
                ballot=ballot,
                source=message,
            )
        if self.request.headers.get("x-requested-with") == "XMLHttpRequest":
            return JsonResponse({"locked": ballot.candidates_locked})
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

    queryset = Ballot.objects.all().select_related("sopn").exclude(sopn=None)
    slug_url_kwarg = "ballot_id"
    slug_field = "ballot_paper_id"
    template_name = "elections/sopn_for_ballot.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # TODO FK between BallotSOPN and ElectionSOPN
        # context["documents_with_same_source"] = OfficialDocument.objects.filter(
        #     source_url=self.object.sopn.source_url
        # )
        context["textract_parsed"] = getattr(
            self.object.sopn, "awstextractparsedsopn", None
        )

        return context


class SOPNForElectionView(DetailView):
    queryset = Election.objects.all().select_related("electionsopn")
    slug_url_kwarg = "election_id"
    slug_field = "slug"
    template_name = "elections/sopn_for_election.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["ballots"] = self.object.ballot_set.order_by("post__label")
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


class BallotsForSelectAjaxView(View):
    @method_decorator(cache_page(60))
    @method_decorator(cache_control(max_age=60))
    def get(self, request, *args, **kwargs):
        qs = (
            Ballot.objects.filter(election__current=True)
            .select_related("election", "post")
            .order_by(
                "election__election_date", "election__name", "post__label"
            )
        )
        partyset_ids = dict(PartySet.objects.values_list("pk", "slug"))
        data = []
        election_name = None
        for ballot in qs:
            partyset_slug = partyset_ids[ballot.post.party_set_id].upper()
            if ballot.election.name != election_name:
                election_name = ballot.election.name
                if data:
                    data.append("</optgroup>")
                data.append(f"<optgroup label='{election_name}'>")

            option_attrs = {
                "value": ballot.ballot_paper_id,
                "data-party-register": partyset_slug,
                "data-uses-party-lists": ballot.election.party_lists_in_use,
            }

            ballot_label = ballot.post.label
            if ballot.cancelled:
                ballot_label = f"{ballot_label} {ballot.cancelled_status_text}"
            if ballot.candidates_locked:
                ballot_label = f"{ballot_label} {ballot.locked_status_text}"
                option_attrs["disabled"] = True

            attrs_str = " ".join(
                [f"{k}='{v}'" for k, v in option_attrs.items()]
            )
            data.append(f"<option {attrs_str}>" f"{ballot_label}" f"</option>")
        data.append("</optgroup>")
        # empty option needs to be included for select2 to display a placeholder
        # see https://select2.org/placeholders#single-select-placeholders
        #  https://github.com/DemocracyClub/yournextrepresentative/issues/1435
        data.insert(0, "<option></option>")
        return HttpResponse("\n".join(data))
