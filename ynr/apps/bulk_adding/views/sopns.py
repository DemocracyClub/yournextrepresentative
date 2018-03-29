# -*- coding: utf-8 -*-

from __future__ import unicode_literals

from braces.views import LoginRequiredMixin
from django.contrib import messages
from django.core.urlresolvers import reverse
from django.db import transaction
from django.db.models import F
from django.http import HttpResponseRedirect
from django.utils.text import slugify
from django.views.generic import RedirectView, TemplateView
from popolo.models import Membership, Organization, Person

from bulk_adding import forms
from candidates.models import (LoggedAction, MembershipExtra, PersonExtra,
                               PostExtra, PostExtraElection,
                               raise_if_unsafe_to_delete)
from candidates.models.auth import check_creation_allowed
from candidates.views.version_data import get_change_metadata, get_client_ip
from elections.models import Election
from moderation_queue.models import SuggestedPostLock
from official_documents.models import OfficialDocument
from official_documents.views import get_add_from_document_cta_flash_message


class BulkAddSOPNRedirectView(RedirectView):
    def get_redirect_url(self, *args, **kwargs):
        return reverse('bulk_add_from_sopn', kwargs={
            'election': kwargs['election'],
            'post_id': kwargs['post_id'],
        })


class BaseSOPNBulkAddView(LoginRequiredMixin, TemplateView):
    # required_group_name = models.TRUSTED_TO_BULK_ADD_GROUP_NAME

    def add_election_and_post_to_context(self, context):
        context['post_extra'] = PostExtra.objects.get(
            slug=context['post_id'])
        context['election_obj'] = Election.objects.get(
            slug=context['election'])
        context['post_election'] = \
            context['election_obj'].postextraelection_set.get(
                postextra=context['post_extra'])
        context['parties'] = context['post_extra'].party_set.party_choices(
            exclude_deregistered=True, include_description_ids=True)
        context['official_document'] = OfficialDocument.objects.filter(
            post__extra__slug=context['post_id'],
            election__slug=context['election'],
            ).first()
        self.official_document = context['official_document']
        return context

    def remaining_posts_for_sopn(self):
        return OfficialDocument.objects.filter(
            source_url=self.official_document.source_url,
            post__extra__postextraelection__election=F('election'),
            post__extra__postextraelection__suggestedpostlock=None,
        )

    def post(self, request, *args, **kwargs):
        context = self.get_context_data(**kwargs)
        if context['formset'].is_valid():
            return self.form_valid(context)
        else:
            return self.form_invalid(context)


class BulkAddSOPNView(BaseSOPNBulkAddView):
    template_name = "bulk_add/sopns/add_form.html"

    def get_context_data(self, **kwargs):
        context = super(BulkAddSOPNView, self).get_context_data(**kwargs)
        context.update(self.add_election_and_post_to_context(context))

        form_kwargs = {
            'parties': context['parties'],
        }

        if 'official_document' in context and \
                context['official_document'] is not None:
            form_kwargs['source'] = context['official_document'].source_url

        if self.request.POST:
            context['formset'] = forms.BulkAddFormSet(
                self.request.POST, **form_kwargs
            )
        else:
            context['formset'] = forms.BulkAddFormSet(
                **form_kwargs
            )

        people_set = set()
        for membership in context['post_extra'].base.memberships.filter(
                extra__election=context['election_obj']):
            person = membership.person
            person.party = membership.on_behalf_of
            people_set.add(person)

        known_people = list(people_set)
        known_people.sort(key=lambda i: i.name.split(' ')[-1])
        context['known_people'] = known_people

        return context

    def form_valid(self, context):
        self.request.session['bulk_add_data'] = context['formset'].cleaned_data
        return HttpResponseRedirect(
            reverse('bulk_add_sopn_review', kwargs={
                'election': context['election'],
                'post_id': context['post_id'],
            })
        )

    def form_invalid(self, context):
        return self.render_to_response(context)


class BulkAddSOPNReviewView(BaseSOPNBulkAddView):
    template_name = "bulk_add/sopns/add_review_form.html"

    def get_context_data(self, **kwargs):
        context = super(BulkAddSOPNReviewView, self).get_context_data(**kwargs)
        context.update(self.add_election_and_post_to_context(context))

        initial = []

        for form in self.request.session['bulk_add_data']:
            if form:
                if '__' in form['party']:
                    org_id, other_name_id = form['party'].split('__')
                    org = Organization.objects.get(pk=org_id)
                    desc = org.other_names.get(pk=other_name_id)
                else:
                    desc = Organization.objects.get(pk=form['party']).name

                form['party_description'] = desc
                initial.append(form)

        if self.request.POST:
            context['formset'] = forms.BulkAddReviewFormSet(
                self.request.POST, parties=context['parties']
            )
        else:
            context['formset'] = forms.BulkAddReviewFormSet(
                initial=initial, parties=context['parties']
            )
        return context

    def add_person(self, person_data):
        # TODO Move this out of the view layer
        person = Person.objects.create(name=person_data['name'])
        person_extra = PersonExtra.objects.create(base=person)
        check_creation_allowed(
            self.request.user, person_extra.current_candidacies
        )

        change_metadata = get_change_metadata(
            self.request, person_data['source']
        )

        person_extra.record_version(change_metadata)
        person_extra.save()

        LoggedAction.objects.create(
            user=self.request.user,
            person=person,
            action_type='person-create',
            ip_address=get_client_ip(self.request),
            popit_person_new_version=change_metadata['version_id'],
            source=change_metadata['information_source'],
        )

        return person_extra

    def update_person(self, context, data, person_extra):
        party = Organization.objects.get(pk=data['party'].split('__')[0])
        post = context['post_extra'].base
        election = Election.objects.get(slug=context['election'])
        pee = election.postextraelection_set.get(
            postextra=context['post_extra'])

        person_extra.not_standing.remove(election)

        membership, _ = Membership.objects.update_or_create(
            post=post,
            person=person_extra.base,
            extra__election=election,
            role=election.candidate_membership_role,
            defaults={
                'on_behalf_of': party,
            }
        )

        MembershipExtra.objects.get_or_create(
            base=membership,
            post_election=pee,
            defaults={
                'party_list_position': None,
                'election': election,
                'elected': None,
            }
        )

        # Now remove other memberships in this election for that
        # person, although we raise an exception if there is any
        # object (other than its MembershipExtra) that has a
        # ForeignKey to the membership, since that would result in
        # losing data.
        qs = Membership.objects \
            .exclude(pk=membership.pk) \
            .filter(
                person=person_extra.base,
                extra__election=election,
                role=election.candidate_membership_role,
            )
        for old_membership in qs:
            raise_if_unsafe_to_delete(old_membership)
            old_membership.delete()

        change_metadata = get_change_metadata(
            self.request, data['source']
        )

        person_extra.record_version(change_metadata)
        person_extra.save()

        LoggedAction.objects.create(
            user=self.request.user,
            person=person_extra.base,
            action_type='person-update',
            ip_address=get_client_ip(self.request),
            popit_person_new_version=change_metadata['version_id'],
            source=change_metadata['information_source'],
        )

    def form_valid(self, context):

        with transaction.atomic():
            for person_form in context['formset']:
                data = person_form.cleaned_data
                if data.get('select_person') == "_new":
                    # Add a new person
                    person_extra = self.add_person(data)
                else:
                    person_extra = PersonExtra.objects.get(
                        base__pk=int(data['select_person']))
                self.update_person(context, data, person_extra)
            if self.request.POST.get('suggest_locking') == 'on':
                pee = PostExtraElection.objects.get(
                    postextra=context['post_extra'],
                    election=Election.objects.get(slug=context['election']),
                )
                SuggestedPostLock.objects.create(
                    user=self.request.user,
                    postextraelection=pee,
                )
        if self.remaining_posts_for_sopn().exists():
            messages.add_message(
                self.request,
                messages.SUCCESS,
                get_add_from_document_cta_flash_message(
                    self.official_document,
                    self.remaining_posts_for_sopn()
                ),
                extra_tags='safe do-something-else'
            )

            url = reverse('posts_for_document', kwargs={
                'pk': self.official_document.pk
            })
        else:
            url = reverse('constituency', kwargs={
                'election': context['election'],
                'post_id': context['post_extra'].slug,
                'ignored_slug': slugify(context['post_extra'].base.label),
            })
        return HttpResponseRedirect(url)

    def form_invalid(self, context):
        return self.render_to_response(context)
