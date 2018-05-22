from __future__ import unicode_literals

from django.views.generic import FormView
from django.utils.translation import ugettext as _
from django.shortcuts import get_object_or_404
from django.db import transaction
from django.http import JsonResponse

from braces.views import LoginRequiredMixin

from auth_helpers.views import user_in_group

from popolo.models import Membership, Person, Post
from candidates.models import MembershipExtra, raise_if_unsafe_to_delete
from candidates.models.constraints import check_no_candidancy_for_election

from elections.mixins import ElectionMixin

from .helpers import get_redirect_to_post
from .version_data import get_client_ip, get_change_metadata
from ..forms import CandidacyCreateForm, CandidacyDeleteForm
from ..models import LoggedAction, TRUSTED_TO_LOCK_GROUP_NAME


def raise_if_locked(request, post, election):
    # If you're a user who's trusted to toggle the constituency lock,
    # they're allowed to edit candidacy:
    if user_in_group(request.user, TRUSTED_TO_LOCK_GROUP_NAME):
        return
    # Otherwise, if the constituency is locked, raise an exception:
    if post.extra.postextraelection_set.get(election=election).candidates_locked:
        raise Exception(_("Attempt to edit a candidacy in a locked constituency"))


class CandidacyView(ElectionMixin, LoginRequiredMixin, FormView):

    form_class = CandidacyCreateForm
    template_name = 'candidates/candidacy-create.html'

    def form_valid(self, form):
        post_id = form.cleaned_data['post_id']
        with transaction.atomic():
            post = get_object_or_404(Post, extra__slug=post_id)
            raise_if_locked(self.request, post, self.election_data)
            change_metadata = get_change_metadata(
                self.request, form.cleaned_data['source']
            )
            person = get_object_or_404(Person, id=form.cleaned_data['person_id'])
            LoggedAction.objects.create(
                user=self.request.user,
                action_type='candidacy-create',
                ip_address=get_client_ip(self.request),
                popit_person_new_version=change_metadata['version_id'],
                person=person,
                source=change_metadata['information_source'],
            )

            membership_exists = Membership.objects.filter(
                person=person,
                post=post,
                role=self.election_data.candidate_membership_role,
                extra__post_election__election=self.election_data
            ).exists()

            person.extra.not_standing.remove(self.election_data)

            if not membership_exists:
                membership = Membership.objects.create(
                    person=person,
                    post=post,
                    role=self.election_data.candidate_membership_role,
                    on_behalf_of=person.extra.last_party(),
                )
                MembershipExtra.objects.create(
                    base=membership,
                    post_election=self.election_data.postextraelection_set.get(
                        postextra=post.extra
                    ),
                )

            person.extra.record_version(change_metadata)
            person.extra.save()
        return get_redirect_to_post(self.election, post)

    def get_context_data(self, **kwargs):
        context = super(CandidacyView, self).get_context_data(**kwargs)
        context['person'] = get_object_or_404(Person, id=self.request.POST.get('person_id'))
        post = get_object_or_404(Post, extra__slug=self.request.POST.get('post_id'))
        context['post_label'] = post.label
        return context


class CandidacyDeleteView(ElectionMixin, LoginRequiredMixin, FormView):

    form_class = CandidacyDeleteForm
    template_name = 'candidates/candidacy-delete.html'

    def form_valid(self, form):
        post_id = form.cleaned_data['post_id']
        with transaction.atomic():
            post = get_object_or_404(Post, extra__slug=post_id)
            raise_if_locked(self.request, post, self.election_data)
            change_metadata = get_change_metadata(
                self.request, form.cleaned_data['source']
            )
            person = get_object_or_404(Person, id=form.cleaned_data['person_id'])
            LoggedAction.objects.create(
                user=self.request.user,
                action_type='candidacy-delete',
                ip_address=get_client_ip(self.request),
                popit_person_new_version=change_metadata['version_id'],
                person=person,
                source=change_metadata['information_source'],
            )

            memberships_to_delete = person.memberships.filter(
                post=post,
                role=self.election_data.candidate_membership_role,
                extra__post_election__election=self.election_data,
            )
            for m in memberships_to_delete:
                raise_if_unsafe_to_delete(m)
                m.delete()

            check_no_candidancy_for_election(person, self.election_data)
            person.extra.not_standing.add(self.election_data)

            person.extra.record_version(change_metadata)
            person.extra.save()
        if self.request.is_ajax():
            return JsonResponse({'success': True})
        return get_redirect_to_post(self.election, post)

    def form_invalid(self, form):
        result = super(
            CandidacyDeleteView, self
        ).form_invalid(form)
        if self.request.is_ajax():
            data = {
                'success': False,
                'errors': form.errors
            }
            return JsonResponse(data)

        return result

    def get_context_data(self, **kwargs):
        context = super(CandidacyDeleteView, self).get_context_data(**kwargs)
        context['person'] = get_object_or_404(Person, id=self.request.POST.get('person_id'))
        post = get_object_or_404(Post, extra__slug=self.request.POST.get('post_id'))
        context['post_label'] = post.label
        return context
