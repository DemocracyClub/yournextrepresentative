from django.http import HttpResponseRedirect
from django.views.generic import FormView, View
from django.shortcuts import get_object_or_404
from django.db import transaction

from candidates.views.helpers import get_max_winners
from elections.mixins import ElectionMixin
from auth_helpers.views import GroupRequiredMixin
from .helpers import get_redirect_to_post
from .version_data import get_client_ip, get_change_metadata
from candidates.forms import ConstituencyRecordWinnerForm
from ..models import RESULT_RECORDERS_GROUP_NAME, LoggedAction, Ballot
from results.models import ResultEvent

from popolo.models import Membership, Post
from people.models import Person


class ConstituencyRecordWinnerView(ElectionMixin, GroupRequiredMixin, FormView):

    form_class = ConstituencyRecordWinnerForm
    template_name = "candidates/record-winner.html"
    required_group_name = RESULT_RECORDERS_GROUP_NAME

    def dispatch(self, request, *args, **kwargs):

        person_id = self.request.POST.get(
            "person_id", self.request.GET.get("person", "")
        )
        self.election_data = self.get_election()
        self.person = get_object_or_404(Person, id=person_id)
        self.post_data = get_object_or_404(Post, slug=self.kwargs["post_id"])
        self.ballot = Ballot.objects.get(
            election=self.election_data, post=self.post_data
        )
        return super().dispatch(request, *args, **kwargs)

    def get_initial(self):
        initial = super().get_initial()
        initial["person_id"] = self.person.id
        return initial

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["post_id"] = self.kwargs["post_id"]
        context["ballot"] = self.ballot
        context["constituency_name"] = self.post_data.label
        context["person"] = self.person
        return context

    def form_valid(self, form):
        change_metadata = get_change_metadata(
            self.request, form.cleaned_data["source"]
        )

        with transaction.atomic():
            number_of_existing_winners = self.post_data.memberships.filter(
                elected=True, post_election__election=self.election_data
            ).count()
            max_winners = get_max_winners(self.ballot)
            if max_winners >= 0 and number_of_existing_winners >= max_winners:
                msg = (
                    "There were already {n} winners of {post_label}"
                    "and the maximum in election {election_name} is {max}"
                )
                raise Exception(
                    msg.format(
                        n=number_of_existing_winners,
                        post_label=self.post_data.label,
                        election_name=self.election_data.name,
                        max=self.election_data.people_elected_per_post,
                    )
                )
            # So now we know we can set this person as the winner:
            candidate_role = self.election_data.candidate_membership_role
            membership_new_winner = Membership.objects.get(
                role=candidate_role,
                post=self.post_data,
                person=self.person,
                post_election__election=self.election_data,
            )
            membership_new_winner.elected = True
            membership_new_winner.save()

            ResultEvent.objects.create(
                election=self.election_data,
                winner=self.person,
                old_post_id=self.post_data.slug,
                old_post_name=self.post_data.label,
                post=self.post_data,
                winner_party=membership_new_winner.party,
                source=form.cleaned_data["source"],
                user=self.request.user,
                parlparse_id=self.person.get_single_identifier_value(
                    "theyworkforyou"
                )
                or "",
            )

            self.person.record_version(change_metadata)
            self.person.save()

            LoggedAction.objects.create(
                user=self.request.user,
                action_type="set-candidate-elected",
                ip_address=get_client_ip(self.request),
                popit_person_new_version=change_metadata["version_id"],
                person=self.person,
                source=change_metadata["information_source"],
            )

            # Now, if the current number of winners is equal to the
            # maximum number of winners, we can set everyone else as
            # "not elected".
            if max_winners >= 0:
                max_reached = max_winners == (number_of_existing_winners + 1)
                if max_reached:
                    losing_candidacies = self.post_data.memberships.filter(
                        post_election__election=self.election_data
                    ).exclude(elected=True)
                    for candidacy in losing_candidacies:
                        if candidacy.elected != False:
                            candidacy.elected = False
                            candidacy.save()
                            candidate = candidacy.person
                            change_metadata = get_change_metadata(
                                self.request,
                                'Setting as "not elected" by implication',
                            )
                            candidate.record_version(change_metadata)
                            candidate.save()

        return get_redirect_to_post(self.election_data, self.post_data)


class ConstituencyRetractWinnerView(ElectionMixin, GroupRequiredMixin, View):

    required_group_name = RESULT_RECORDERS_GROUP_NAME
    http_method_names = ["post"]

    def post(self, request, *args, **kwargs):
        post_id = self.kwargs["post_id"]
        with transaction.atomic():
            post = get_object_or_404(Post, slug=post_id)
            constituency_name = post.short_label

            all_candidacies = post.memberships.filter(
                role=self.election_data.candidate_membership_role,
                post_election__election=self.election_data,
            )
            source = "Result recorded in error, retracting"
            for candidacy in all_candidacies.all():
                if candidacy.elected:
                    # If elected is True then a ResultEvent will have
                    # been created and been included in the feed, so
                    # we need to create a corresponding retraction
                    # ResultEvent.
                    ResultEvent.objects.create(
                        election=self.election_data,
                        winner=candidacy.person,
                        old_post_id=candidacy.post.slug,
                        old_post_name=candidacy.post.label,
                        post=candidacy.post,
                        winner_party=candidacy.party,
                        source=source,
                        user=self.request.user,
                        parlparse_id=candidacy.person.get_single_identifier_value(
                            "theyworkforyou"
                        )
                        or "",
                        retraction=True,
                    )
                if candidacy.elected is not None:
                    candidacy.elected = None
                    candidacy.save()
                    candidate = candidacy.person
                    change_metadata = get_change_metadata(self.request, source)
                    candidate.record_version(change_metadata)
                    candidate.save()

        return HttpResponseRedirect(
            self.election_data.ballot_set.get(
                post__slug=post_id
            ).get_absolute_url()
        )
