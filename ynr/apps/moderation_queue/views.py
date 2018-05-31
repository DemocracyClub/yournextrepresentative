# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import bleach
import os
import re
import random

from os.path import join
from tempfile import NamedTemporaryFile

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.contrib.sites.models import Site
from django.contrib import messages
from django.core.files import File
from django.core.mail import send_mail
from django.core.urlresolvers import reverse
from django.db import models
from django.http import HttpResponseRedirect, HttpResponseBadRequest
from django.shortcuts import render, get_object_or_404
from django.template.loader import render_to_string
from django.utils.http import urlquote
from django.utils.translation import ugettext as _
from django.views.generic import ListView, TemplateView, CreateView
from PIL import Image as PillowImage
from braces.views import LoginRequiredMixin
from slugify import slugify

from auth_helpers.views import GroupRequiredMixin

from .forms import UploadPersonPhotoImageForm, UploadPersonPhotoURLForm, PhotoReviewForm
from .models import QueuedImage, SuggestedPostLock, PHOTO_REVIEWERS_GROUP_NAME

from candidates.management.images import (
    get_file_md5sum, ImageDownloadException, download_image_from_url)
from candidates.models import (LoggedAction, ImageExtra,
                               PersonExtra, PostExtraElection)
from candidates.views.version_data import get_client_ip, get_change_metadata

from popolo.models import Person


@login_required
def upload_photo(request, person_id):
    person = get_object_or_404(Person, id=person_id)
    image_form = UploadPersonPhotoImageForm(initial={'person': person})
    url_form = UploadPersonPhotoURLForm(initial={'person': person})
    return render(
        request,
        'moderation_queue/photo-upload-new.html',
        {
            'image_form': image_form,
            'url_form': url_form,
            'queued_images': QueuedImage.objects.filter(
                person=person,
                decision='undecided',
            ).order_by('created'),
            'person': person
        }
    )


@login_required
def upload_photo_image(request, person_id):
    person = get_object_or_404(Person, id=person_id)
    image_form = UploadPersonPhotoImageForm(request.POST, request.FILES)
    url_form = UploadPersonPhotoURLForm(initial={'person': person})
    if image_form.is_valid():
        # Make sure that we save the user that made the upload
        queued_image = image_form.save(commit=False)
        queued_image.user = request.user
        queued_image.save()
        # Record that action:
        LoggedAction.objects.create(
            user=request.user,
            action_type='photo-upload',
            ip_address=get_client_ip(request),
            popit_person_new_version='',
            person=person,
            source=image_form.cleaned_data['justification_for_use'],
        )
        return HttpResponseRedirect(reverse(
            'photo-upload-success',
            kwargs={
                'person_id': person.id
            }
        ))

    return render(
        request,
        'moderation_queue/photo-upload-new.html',
        {
            'image_form': image_form,
            'url_form': url_form,
            'queued_images': QueuedImage.objects.filter(
                person=person,
                decision='undecided',
            ).order_by('created'),
            'person': person
        }
    )


@login_required
def upload_photo_url(request, person_id):
    person = get_object_or_404(Person, id=person_id)
    image_form = UploadPersonPhotoImageForm(initial={'person': person})
    url_form = UploadPersonPhotoURLForm(request.POST)

    if url_form.is_valid():
        image_url = url_form.cleaned_data['image_url']
        try:
            img_temp_filename = download_image_from_url(image_url)
        except ImageDownloadException as ide:
            return HttpResponseBadRequest(unicode(ide).encode('utf-8'))
        try:
            queued_image = QueuedImage(
                why_allowed=url_form.cleaned_data['why_allowed_url'],
                justification_for_use=url_form.cleaned_data['justification_for_use_url'],
                person=person,
                user=request.user
            )
            queued_image.save()
            with open(img_temp_filename , 'rb') as f:
                queued_image.image.save(image_url, File(f))
            queued_image.save()
            LoggedAction.objects.create(
                user=request.user,
                action_type='photo-upload',
                ip_address=get_client_ip(request),
                popit_person_new_version='',
                person=person,
                source=url_form.cleaned_data['justification_for_use_url'],
            )
            return HttpResponseRedirect(reverse(
                'photo-upload-success',
                kwargs={
                    'person_id': person.id
                }
            ))
        finally:
            os.remove(img_temp_filename)
    else:
        return render(
            request,
            'moderation_queue/photo-upload-new.html',
            {
                'image_form': image_form,
                'url_form': url_form,
                'queued_images': QueuedImage.objects.filter(
                    person=person,
                    decision='undecided',
                ).order_by('created'),
                'person': person
            }
        )


class PhotoUploadSuccess(TemplateView):
    template_name = 'moderation_queue/photo-upload-success.html'

    def get_context_data(self, **kwargs):
        context = super(PhotoUploadSuccess, self).get_context_data(**kwargs)
        context['person'] = Person.objects.get(
            id=kwargs['person_id']
        )
        return context


class PhotoReviewList(GroupRequiredMixin, ListView):
    template_name = 'moderation_queue/photo-review-list.html'
    required_group_name = PHOTO_REVIEWERS_GROUP_NAME

    def get_queryset(self):
        return QueuedImage.objects. \
            filter(decision='undecided'). \
            order_by('created'). \
            select_related('user', 'person',)


def tidy_party_name(name):
    """If a party name contains an initialism in brackets, use that instead

    >>> tidy_party_name('Hello World Party (HWP)') == 'HWP'
    True
    >>> tidy_party_name('Hello World Party') == 'Hello World Party'
    True
    """
    m = re.search(r'\(([A-Z]+)\)', name)
    if m:
        return m.group(1)
    return name


def value_if_none(v, default):
    return default if v is None else v


class PhotoReview(GroupRequiredMixin, TemplateView):
    """The class-based view for approving or rejecting a particular photo"""

    template_name = 'moderation_queue/photo-review.html'
    http_method_names = ['get', 'post']
    required_group_name = PHOTO_REVIEWERS_GROUP_NAME

    def get_google_image_search_url(self, person):
        image_search_query = '"{0}"'.format(person.name)
        last_candidacy = person.extra.last_candidacy
        if last_candidacy:
            party = last_candidacy.on_behalf_of
            if party:
                image_search_query += ' "{0}"'.format(
                    tidy_party_name(party.name)
                )
            post = last_candidacy.post
            if post is not None:
                image_search_query += ' "{0}"'.format(post.label)
        return 'https://www.google.co.uk/search?tbm=isch&q={0}'.format(
            urlquote(image_search_query)
        )

    def get_google_reverse_image_search_url(self, image_url):
        url = 'https://www.google.com/searchbyimage?&image_url='
        absolute_image_url = self.request.build_absolute_uri(image_url)
        return url + urlquote(absolute_image_url)

    def get_context_data(self, **kwargs):
        context = super(PhotoReview, self).get_context_data(**kwargs)
        self.queued_image = get_object_or_404(
            QueuedImage,
            pk=kwargs['queued_image_id']
        )
        context['queued_image'] = self.queued_image
        if context['queued_image'].user:
            username = context['queued_image'].user.username
            email = context['queued_image'].user.email
        else:
            username = "a robot 🤖"
            email = None
        context['username'] = username
        context['email'] = email
        person = Person.objects.get(
            id=self.queued_image.person.id,
        )
        context['has_crop_bounds'] = int(self.queued_image.has_crop_bounds)
        max_x = self.queued_image.image.width - 1
        max_y = self.queued_image.image.height - 1
        guessed_crop_bounds = [
            value_if_none(self.queued_image.crop_min_x, 0),
            value_if_none(self.queued_image.crop_min_y, 0),
            value_if_none(self.queued_image.crop_max_x, max_x),
            value_if_none(self.queued_image.crop_max_y, max_y),
        ]
        context['form'] = PhotoReviewForm(
            initial={
                'queued_image_id': self.queued_image.id,
                'decision': self.queued_image.decision,
                'x_min': guessed_crop_bounds[0],
                'y_min': guessed_crop_bounds[1],
                'x_max': guessed_crop_bounds[2],
                'y_max': guessed_crop_bounds[3],
                'moderator_why_allowed': self.queued_image.why_allowed,
                'make_primary': True,
            }
        )
        context['guessed_crop_bounds'] = guessed_crop_bounds
        context['why_allowed'] = self.queued_image.why_allowed
        context['moderator_why_allowed'] = self.queued_image.why_allowed
        # There are often source links supplied in the justification,
        # and it's convenient to be able to follow them. However, make
        # sure that any maliciously added HTML tags have been stripped
        # before linkifying any URLs:
        context['justification_for_use'] = bleach.linkify(
            bleach.clean(
                self.queued_image.justification_for_use,
                tags=[],
                strip=True
            )
        )
        context['google_image_search_url'] = self.get_google_image_search_url(
            person
        )
        context['google_reverse_image_search_url'] = \
            self.get_google_reverse_image_search_url(
                self.queued_image.image.url
        )
        context['person'] = person
        return context

    def send_mail(self, subject, message, email_support_too=False):
        if not self.queued_image.user:
            # We can't send emails to bots…yet.
            return
        recipients = [self.queued_image.user.email]
        if email_support_too:
            recipients.append(settings.SUPPORT_EMAIL)
        return send_mail(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,
            recipients,
            fail_silently=False,
        )

    def crop_and_upload_image_to_popit(self, image_filename, crop_bounds, moderator_why_allowed, make_primary):
        original = PillowImage.open(image_filename)
        # Some uploaded images are CYMK, which gives you an error when
        # you try to write them as PNG, so convert to RGBA (this is
        # RGBA rather than RGB so that any alpha channel (transparency)
        # is preserved).
        person_id = self.queued_image.person.id
        person_extra = PersonExtra.objects.get(base__id=person_id)
        original = original.convert('RGBA')
        cropped = original.crop(crop_bounds)
        ntf = NamedTemporaryFile(delete=False)
        cropped.save(ntf.name, 'PNG')
        md5sum = get_file_md5sum(ntf.name)
        filename = str(person_id) + '.png'
        if self.queued_image.user:
            uploaded_by = self.queued_image.user.username
        else:
            uploaded_by = _("a script")
        source = _(
            'Uploaded by {uploaded_by}: Approved from photo moderation queue'
        ).format(uploaded_by=uploaded_by)

        ImageExtra.objects.create_from_file(
            ntf.name,
            join('images', filename),
            base_kwargs={
                'source': source,
                'is_primary': make_primary,
                'content_object': person_extra,
            },
            extra_kwargs={
                'md5sum': md5sum,
                'uploading_user': self.queued_image.user,
                'user_notes': self.queued_image.justification_for_use,
                'copyright': moderator_why_allowed,
                'user_copyright': self.queued_image.why_allowed,
                'notes': _('Approved from photo moderation queue'),
            },
        )

    def form_valid(self, form):
        decision = form.cleaned_data['decision']
        person = Person.objects.get(
            id=self.queued_image.person.id
        )
        person_extra = person.extra
        candidate_path = person_extra.get_absolute_url()
        candidate_name = person.name
        candidate_link = '<a href="{url}">{name}</a>'.format(
            url=candidate_path,
            name=candidate_name,
        )
        photo_review_url = self.request.build_absolute_uri(
            self.queued_image.get_absolute_url()
        )
        site_name = Site.objects.get_current().name

        def flash(level, message):
            messages.add_message(
                self.request,
                level,
                message,
                extra_tags='safe photo-review'
            )
        if self.queued_image.user:
            uploaded_by = self.queued_image.user.username
        else:
            uploaded_by = _("a script")

        if decision == 'approved':
            # Crop the image...
            crop_fields = ('x_min', 'y_min', 'x_max', 'y_max')
            self.crop_and_upload_image_to_popit(
                self.queued_image.image.path,
                [form.cleaned_data[e] for e in crop_fields],
                form.cleaned_data['moderator_why_allowed'],
                form.cleaned_data['make_primary'],
            )
            self.queued_image.decision = 'approved'
            for i, field in enumerate(crop_fields):
                setattr(
                    self.queued_image,
                    'crop_' + field,
                    form.cleaned_data[field]
                )
            self.queued_image.save()

            sentence = 'Approved a photo upload from {uploading_user}'
            ' who provided the message: "{message}"'

            update_message = _(sentence).format(
                uploading_user=uploaded_by,
                message=self.queued_image.justification_for_use,
            )
            change_metadata = get_change_metadata(
                self.request,
                update_message
            )
            person_extra.record_version(change_metadata)
            person_extra.save()
            person.save()
            LoggedAction.objects.create(
                user=self.request.user,
                action_type='photo-approve',
                ip_address=get_client_ip(self.request),
                popit_person_new_version=change_metadata['version_id'],
                person=person,
                source=update_message,
            )
            candidate_full_url = self.request.build_absolute_uri(
                person_extra.get_absolute_url(self.request)
            )

            self.send_mail(
                _('{site_name} image upload approved').format(
                    site_name=site_name
                ),
                render_to_string(
                    'moderation_queue/photo_approved_email.txt',
                    {
                        'site_name': site_name,
                        'candidate_page_url': candidate_full_url,
                        'intro': _(
                            "Thank-you for submitting a photo to "
                            "{site_name}; that's been uploaded now for "
                            "the candidate page here:"
                        ).format(site_name=site_name),
                        'signoff': _(
                            "Many thanks from the {site_name} volunteers"
                        ).format(site_name=site_name),
                    }
                ),
            )
            flash(
                messages.SUCCESS,
                _('You approved a photo upload for %s') % candidate_link
            )
        elif decision == 'rejected':
            self.queued_image.decision = 'rejected'
            self.queued_image.save()

            sentence = 'Rejected a photo upload from {uploading_user}'

            update_message = _(sentence).format(
                uploading_user=uploaded_by,
            )
            LoggedAction.objects.create(
                user=self.request.user,
                action_type='photo-reject',
                ip_address=get_client_ip(self.request),
                popit_person_new_version='',
                person=person,
                source=update_message,
            )
            retry_upload_link = self.request.build_absolute_uri(
                reverse(
                    'photo-upload',
                    kwargs={'person_id': self.queued_image.person.id}
                )
            )
            self.send_mail(
                _('{site_name} image moderation results').format(
                    site_name=Site.objects.get_current().name
                ),
                render_to_string(
                    'moderation_queue/photo_rejected_email.txt',
                    {
                        'reason': form.cleaned_data['rejection_reason'],
                        'retry_upload_link': retry_upload_link,
                        'photo_review_url': photo_review_url,
                        'intro': _(
                            "Thank-you for uploading a photo of "
                            "{candidate_name} to {site_name}, "
                            "but unfortunately we can't use that image because:"
                        ).format(
                            candidate_name=candidate_name,
                            site_name=site_name
                        ),
                        'possible_actions': _(
                            'You can just reply to this email if you want to '
                            'discuss that further, or you can try uploading a '
                            'photo with a different reason or justification '
                            'for its use using this link:'
                        ),
                        'signoff': _(
                            "Many thanks from the {site_name} volunteers"
                        ).format(site_name=site_name),
                    },
                ),
                email_support_too=True,
            )
            flash(
                messages.INFO,
                _('You rejected a photo upload for %s') % candidate_link
            )
        elif decision == 'undecided':
            # If it's left as undecided, just redirect back to the
            # photo review queue...
            flash(
                messages.INFO,
                _('You left a photo upload for {0} in the queue').format(
                    candidate_link
                )
            )
        elif decision == 'ignore':
            self.queued_image.decision = 'ignore'
            self.queued_image.save()

            sentence = 'Ignored a photo upload from {uploading_user}'
            ' (This usually means it was a duplicate)'

            update_message = _(sentence).format(
                uploading_user=uploaded_by)
            LoggedAction.objects.create(
                user=self.request.user,
                action_type='photo-ignore',
                ip_address=get_client_ip(self.request),
                popit_person_new_version='',
                person=person,
                source=update_message,
            )
            flash(
                messages.INFO,
                _('You indicated a photo upload for {0} should be ignored').format(
                    candidate_link
                )
            )
        else:
            raise Exception("BUG: unexpected decision {0}".format(decision))
        return HttpResponseRedirect(reverse('photo-review-list'))

    def form_invalid(self, form):
        return self.render_to_response(
            self.get_context_data(
                queued_image_id=self.queued_image.id,
                form=form
            )
        )

    def post(self, request, *args, **kwargs):
        self.queued_image = QueuedImage.objects.get(
            pk=kwargs['queued_image_id']
        )
        form = PhotoReviewForm(data=self.request.POST)
        if form.is_valid():
            return self.form_valid(form)
        else:
            return self.form_invalid(form)


class SuggestLockView(LoginRequiredMixin, CreateView):
    '''This handles creating a SuggestedPostLock from a form submission'''

    model = SuggestedPostLock
    fields = ['justification', 'postextraelection']

    def form_valid(self, form):
        user = self.request.user
        form.instance.user = user
        messages.add_message(
            self.request,
            messages.SUCCESS,
            message="Thanks for suggesting we lock an area!"
        )

        return super(SuggestLockView, self).form_valid(form)

    def get_success_url(self):
        return reverse('constituency', kwargs={
            'election': self.kwargs['election_id'],
            'post_id': self.object.postextraelection.postextra.slug,
            'ignored_slug': slugify(self.object.postextraelection.postextra.short_label),
        })


class SuggestLockReviewListView(LoginRequiredMixin, TemplateView):
    """
    This is the view which lists all post lock suggestions that need review

    Most people will get to this by clicking on the red highlighted 'Post lock
    suggestions' counter in the header.
    """

    template_name = "moderation_queue/suggestedpostlock_review.html"

    def get_lock_suggestions(self, mine):
        # TODO optimize this
        qs = PostExtraElection.objects.filter(
            election__current=True,
            candidates_locked=False,
        ).exclude(
            suggestedpostlock=None,
            officialdocument=None
        ).select_related(
            'election',
            'postextra',
            'postextra__base',
        ).prefetch_related(
            'officialdocument_set',
            models.Prefetch(
                'suggestedpostlock_set',
                SuggestedPostLock.objects.select_related('user')
            ),
        ).order_by(
            'officialdocument__source_url',
            'postextra__base__label'

        )

        if mine:
            qs = qs.filter(suggestedpostlock__user=self.request.user)
        else:
            qs = qs.exclude(suggestedpostlock__user=self.request.user)

        return qs[:10]

    def get_context_data(self, **kwargs):
        context = super(
            SuggestLockReviewListView, self).get_context_data(**kwargs)
        context['my_suggestions'] = self.get_lock_suggestions(mine=True)
        context['other_suggestions'] = self.get_lock_suggestions(mine=False)
        context['test_pdf_view'] = bool(self.request.GET.get('pdfembed'))

        return context


class SOPNReviewRequiredView(ListView):
    '''List all post that have a nominations paper, but no lock suggestion'''

    template_name = "moderation_queue/sopn-review-required.html"

    def get(self, *args, **kwargs):
        if 'random' in self.request.GET:
            qs = self.get_queryset()
            count = qs.count()
            if count:
                random_offset = random.randrange(count)
                pee = qs[random_offset]
                url = reverse(
                    'bulk_add_from_sopn',
                    args=(
                     pee.election.slug,
                     pee.postextra.slug
                    )

                )
                return HttpResponseRedirect(url)
        return super(SOPNReviewRequiredView, self).get(*args, **kwargs)


    def get_queryset(self):
        """
        PostExtraElection objects with a document but no lock suggestion
        """
        qs = PostExtraElection.objects \
            .filter(
                suggestedpostlock__isnull=True,
                candidates_locked=False,
                election__current=True
            ).exclude(
                officialdocument=None
            ).select_related(
                'postextra__base', 'election'
            ).prefetch_related(
                'officialdocument_set'
            ).order_by(
                'officialdocument__source_url', 'election', 'postextra__base__label'
            )
        return qs



class PersonNameCleanupView(TemplateView):
    template_name = "moderation_queue/person_name_cleanup.html"

    def get_context_data(self, **kwargs):
        context = super(
            PersonNameCleanupView, self).get_context_data(**kwargs)

        people = Person.objects.all().only('name')

        regex = re.compile('[A-Z][A-Z]+')
        context['two_upper'] = [
            p for p in people if regex.search(p.name)
        ]

        return context
