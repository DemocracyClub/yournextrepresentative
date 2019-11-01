from braces.views import LoginRequiredMixin
from django.db import transaction
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.views.generic import FormView

from auth_helpers.views import user_in_group
from candidates.models import raise_if_unsafe_to_delete
from candidates.models.constraints import check_no_candidancy_for_election
from elections.mixins import ElectionMixin
from people.forms import CandidacyCreateForm, CandidacyDeleteForm
from people.models import Person
from popolo.models import Membership, Post

from ..models import TRUSTED_TO_LOCK_GROUP_NAME, LoggedAction
from .helpers import get_redirect_to_post
from .version_data import get_change_metadata, get_client_ip


def raise_if_locked(request, post, election):
    # If you're a user who's trusted to toggle the constituency lock,
    # they're allowed to edit candidacy:
    if user_in_group(request.user, TRUSTED_TO_LOCK_GROUP_NAME):
        return
    # Otherwise, if the constituency is locked, raise an exception:
    if post.ballot_set.get(election=election).candidates_locked:
        raise Exception("Attempt to edit a candidacy in a locked constituency")


class CandidacyView(ElectionMixin, LoginRequiredMixin, FormView):

    form_class = CandidacyCreateForm

    def form_valid(self, form):
        post_id = form.cleaned_data["post_id"]
        with transaction.atomic():
            post = get_object_or_404(Post, slug=post_id)
            raise_if_locked(self.request, post, self.election_data)
            change_metadata = get_change_metadata(
                self.request, form.cleaned_data["source"]
            )
            person = get_object_or_404(
                Person, id=form.cleaned_data["person_id"]
            )
            LoggedAction.objects.create(
                user=self.request.user,
                action_type="candidacy-create",
                ip_address=get_client_ip(self.request),
                popit_person_new_version=change_metadata["version_id"],
                person=person,
                source=change_metadata["information_source"],
            )

            membership_exists = Membership.objects.filter(
                person=person, post=post, ballot__election=self.election_data
            ).exists()

            person.not_standing.remove(self.election_data)

            if not membership_exists:
                Membership.objects.create(
                    person=person,
                    post=post,
                    party=person.last_party(),
                    ballot=self.election_data.ballot_set.get(post=post),
                )

            person.record_version(change_metadata)
            person.save()
        return get_redirect_to_post(self.election_data, post)


class CandidacyDeleteView(ElectionMixin, LoginRequiredMixin, FormView):

    form_class = CandidacyDeleteForm
    template_name = "candidates/candidacy-delete.html"

    def form_valid(self, form):
        post_id = form.cleaned_data["post_id"]
        with transaction.atomic():
            post = get_object_or_404(Post, slug=post_id)
            raise_if_locked(self.request, post, self.election_data)
            change_metadata = get_change_metadata(
                self.request, form.cleaned_data["source"]
            )
            person = get_object_or_404(
                Person, id=form.cleaned_data["person_id"]
            )
            LoggedAction.objects.create(
                user=self.request.user,
                action_type="candidacy-delete",
                ip_address=get_client_ip(self.request),
                popit_person_new_version=change_metadata["version_id"],
                person=person,
                source=change_metadata["information_source"],
            )

            memberships_to_delete = person.memberships.filter(
                post=post, ballot__election=self.election_data
            )
            for m in memberships_to_delete:
                raise_if_unsafe_to_delete(m)
                m.delete()

            check_no_candidancy_for_election(person, self.election_data)
            person.not_standing.add(self.election_data)

            person.record_version(change_metadata)
            person.save()
        if self.request.is_ajax():
            return JsonResponse({"success": True})
        return get_redirect_to_post(self.election_data, post)

    def form_invalid(self, form):
        result = super(CandidacyDeleteView, self).form_invalid(form)
        if self.request.is_ajax():
            data = {"success": False, "errors": form.errors}
            return JsonResponse(data)

        return result

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["person"] = get_object_or_404(
            Person, id=self.request.POST.get("person_id")
        )
        post = get_object_or_404(Post, slug=self.request.POST.get("post_id"))
        context["post_label"] = post.label
        return context
