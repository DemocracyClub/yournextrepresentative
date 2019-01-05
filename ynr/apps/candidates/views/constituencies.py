from slugify import slugify

from django.core.exceptions import ValidationError
from django.core.urlresolvers import reverse
from django.http import HttpResponse, HttpResponseRedirect, JsonResponse
from django.utils.translation import ugettext as _
from django.views.generic import FormView, View
from django.shortcuts import get_object_or_404
from django.db import transaction

from candidates.views.helpers import get_max_winners
from elections.mixins import ElectionMixin
from auth_helpers.views import GroupRequiredMixin
from .helpers import get_redirect_to_post
from .version_data import get_client_ip, get_change_metadata
from ..csv_helpers import list_to_csv, memberships_dicts_for_csv
from candidates.forms import ToggleLockForm, ConstituencyRecordWinnerForm
from ..models import (
    TRUSTED_TO_LOCK_GROUP_NAME,
    RESULT_RECORDERS_GROUP_NAME,
    LoggedAction,
    PostExtraElection,
)
from results.models import ResultEvent

from popolo.models import Membership, Post
from people.models import Person


class ConstituencyDetailCSVView(ElectionMixin, View):

    http_method_names = ["get"]

    def get(self, request, *args, **kwargs):
        post = Post.objects.get(slug=kwargs["post_id"])
        memberships_dict, elected = memberships_dicts_for_csv(
            election_slug=self.election_data.slug, post_slug=post.slug
        )

        filename = "{election}-{constituency_slug}.csv".format(
            election=self.election, constituency_slug=slugify(post.short_label)
        )
        response = HttpResponse(content_type="text/csv")
        response["Content-Disposition"] = 'attachment; filename="%s"' % filename
        response.write(list_to_csv(memberships_dict[self.election_data.slug]))
        return response


class ConstituencyLockView(ElectionMixin, GroupRequiredMixin, View):
    required_group_name = TRUSTED_TO_LOCK_GROUP_NAME

    http_method_names = ["post"]

    def post(self, request, *args, **kwargs):
        form = ToggleLockForm(data=self.request.POST)
        if form.is_valid():
            post_id = form.cleaned_data["post_id"]
            with transaction.atomic():
                post = get_object_or_404(Post, slug=post_id)
                lock = form.cleaned_data["lock"]
                extra_election = PostExtraElection.objects.get(
                    post=post, election__slug=self.election
                )
                extra_election.candidates_locked = lock
                extra_election.save()
                post_name = post.short_label
                if lock:
                    suffix = "-lock"
                    pp = "Locked"
                else:
                    suffix = "-unlock"
                    pp = "Unlocked"
                message = pp + " constituency {} ({})".format(
                    post_name, post.id
                )

                LoggedAction.objects.create(
                    user=self.request.user,
                    action_type=("constituency" + suffix),
                    ip_address=get_client_ip(self.request),
                    source=message,
                )
            if self.request.is_ajax():
                return JsonResponse(
                    {"locked": extra_election.candidates_locked}
                )
            else:
                return HttpResponseRedirect(
                    reverse(
                        "constituency",
                        kwargs={
                            "election": self.election,
                            "post_id": post_id,
                            "ignored_slug": slugify(post_name),
                        },
                    )
                )
        else:
            message = _("Invalid data POSTed to ConstituencyLockView")
            raise ValidationError(message)


class ConstituencyRecordWinnerView(ElectionMixin, GroupRequiredMixin, FormView):

    form_class = ConstituencyRecordWinnerForm
    # TODO: is this template ever used?
    template_name = "candidates/record-winner.html"
    required_group_name = RESULT_RECORDERS_GROUP_NAME

    def dispatch(self, request, *args, **kwargs):

        person_id = self.request.POST.get(
            "person_id", self.request.GET.get("person", "")
        )
        self.election_data = self.get_election()
        self.person = get_object_or_404(Person, id=person_id)
        self.post_data = get_object_or_404(Post, slug=self.kwargs["post_id"])
        self.post_election = PostExtraElection.objects.get(
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
        context["post_election"] = self.post_election
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
            max_winners = get_max_winners(self.post_election)
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
                parlparse_id=self.person.get_identifier("uk.org.publicwhip"),
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
                                _('Setting as "not elected" by implication'),
                            )
                            candidate.record_version(change_metadata)
                            candidate.save()

        return get_redirect_to_post(self.election, self.post_data)


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
            source = _("Result recorded in error, retracting")
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
                        parlparse_id=candidacy.person.get_identifier(
                            "uk.org.publicwhip"
                        ),
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
            reverse(
                "constituency",
                kwargs={
                    "post_id": post_id,
                    "election": self.election,
                    "ignored_slug": slugify(constituency_name),
                },
            )
        )
