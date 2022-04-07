import random
import re

from typing import Any, Dict

import bleach
from braces.views import LoginRequiredMixin
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import models
from django.db.models import Count, Q
from django.http import (
    HttpResponseBadRequest,
    HttpResponseRedirect,
    JsonResponse,
)

from django.shortcuts import get_object_or_404
from django.urls import reverse
from urllib.parse import quote
from django.views.generic import CreateView, ListView, TemplateView, View

from auth_helpers.views import GroupRequiredMixin
from moderation_queue.helpers import (
    ImageDownloadException,
    download_image_from_url,
)

from candidates.models import TRUSTED_TO_LOCK_GROUP_NAME, Ballot, LoggedAction
from candidates.views.version_data import get_client_ip
from candidates.models.db import ActionType
from elections.models import Election
from moderation_queue.filters import QueuedImageFilter
from people.models import Person
from popolo.models import Membership
from moderation_queue.helpers import (
    upload_photo_response,
    image_form_valid_response,
)

from .forms import (
    PhotoReviewForm,
    SuggestedPostLockForm,
    UploadPersonPhotoImageForm,
    UploadPersonPhotoURLForm,
)
from .models import PHOTO_REVIEWERS_GROUP_NAME, QueuedImage, SuggestedPostLock


@login_required
def upload_photo(request, person_id):
    person = get_object_or_404(Person, id=person_id)
    image_form = UploadPersonPhotoImageForm(initial={"person": person})
    url_form = UploadPersonPhotoURLForm(initial={"person": person})
    return upload_photo_response(request, person, image_form, url_form)


@login_required
def upload_photo_image(request, person_id):
    person = get_object_or_404(Person, id=person_id)
    image_form = UploadPersonPhotoImageForm(request.POST, request.FILES)
    url_form = UploadPersonPhotoURLForm(initial={"person": person})
    if image_form.is_valid():
        return image_form_valid_response(
            request=request, person=person, image_form=image_form
        )
    return upload_photo_response(
        request=request, person=person, image_form=image_form, url_form=url_form
    )


@login_required
def upload_photo_url(request, person_id):
    person = get_object_or_404(Person, id=person_id)
    image_form = UploadPersonPhotoImageForm(initial={"person": person})
    url_form = UploadPersonPhotoURLForm(request.POST)

    if not url_form.is_valid():
        return upload_photo_response(
            request=request,
            person=person,
            image_form=image_form,
            url_form=url_form,
        )

    image_url = url_form.cleaned_data["image_url"]
    try:
        image_bytes = download_image_from_url(image_url)
    except ImageDownloadException as ide:
        return HttpResponseBadRequest(str(ide).encode("utf-8"))

    filename = image_url.split("/")[-1]
    extension = filename.split(".")[-1]
    filename = filename.replace(extension, "png")
    queued_image = QueuedImage(
        why_allowed=url_form.cleaned_data["why_allowed_url"],
        justification_for_use=url_form.cleaned_data[
            "justification_for_use_url"
        ],
        person=person,
        user=request.user,
    )
    queued_image.image.save(filename, image_bytes, save=True)
    LoggedAction.objects.create(
        user=request.user,
        action_type=ActionType.PHOTO_UPLOAD,
        ip_address=get_client_ip(request),
        popit_person_new_version="",
        person=person,
        source=url_form.cleaned_data["justification_for_use_url"],
    )
    return HttpResponseRedirect(
        reverse("photo-upload-success", kwargs={"person_id": person.id})
    )


class PhotoUploadSuccess(TemplateView):
    template_name = "moderation_queue/photo-upload-success.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["person"] = Person.objects.get(id=kwargs["person_id"])
        return context


class PhotoReviewList(GroupRequiredMixin, ListView):
    template_name = "moderation_queue/photo-review-list.html"
    required_group_name = PHOTO_REVIEWERS_GROUP_NAME

    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        context = super().get_context_data(**kwargs)
        filter_obj = QueuedImageFilter(
            data=self.request.GET,
            queryset=context["object_list"],
            request=self.request,
        )
        context["filter_obj"] = filter_obj
        context["object_list"] = filter_obj.qs
        context["shortcuts"] = filter_obj.shortcuts

        return context

    def get_queryset(self):
        return (
            QueuedImage.objects.filter(decision="undecided")
            .order_by("created")
            .select_related("user", "person")
        )


def tidy_party_name(name):
    """If a party name contains an initialism in brackets, use that instead

    >>> tidy_party_name('Hello World Party (HWP)') == 'HWP'
    True
    >>> tidy_party_name('Hello World Party') == 'Hello World Party'
    True
    """
    m = re.search(r"\(([A-Z]+)\)", name)
    if m:
        return m.group(1)
    return name


def value_if_none(v, default):
    return default if v is None else v


class PhotoReview(GroupRequiredMixin, TemplateView):
    """The class-based view for approving or rejecting a particular photo"""

    template_name = "moderation_queue/photo-review.html"
    http_method_names = ["get", "post"]
    required_group_name = PHOTO_REVIEWERS_GROUP_NAME

    def get_google_image_search_url(self, person):
        image_search_query = '"{}"'.format(person.name)
        last_candidacy = person.last_candidacy
        if last_candidacy:
            party = last_candidacy.party
            if party:
                image_search_query += ' "{}"'.format(
                    tidy_party_name(party.name)
                )
            post = last_candidacy.ballot.post
            if post is not None:
                image_search_query += ' "{}"'.format(post.label)
        return "https://www.google.co.uk/search?tbm=isch&q={}".format(
            quote(image_search_query)
        )

    def get_google_reverse_image_search_url(self, image_url):
        url = "https://www.google.com/searchbyimage?&image_url="
        absolute_image_url = self.request.build_absolute_uri(image_url)
        return url + quote(absolute_image_url)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        self.queued_image = get_object_or_404(
            QueuedImage, pk=kwargs["queued_image_id"]
        )
        context["queued_image"] = self.queued_image
        if context["queued_image"].user:
            username = context["queued_image"].user.username
            email = context["queued_image"].user.email
        else:
            username = "a robot 🤖"
            email = None
        context["username"] = username
        context["email"] = email
        person = Person.objects.get(id=self.queued_image.person.id)
        context["has_crop_bounds"] = int(self.queued_image.has_crop_bounds)
        max_x = self.queued_image.image.width - 1
        max_y = self.queued_image.image.height - 1
        guessed_crop_bounds = [
            value_if_none(self.queued_image.crop_min_x, 0),
            value_if_none(self.queued_image.crop_min_y, 0),
            value_if_none(self.queued_image.crop_max_x, max_x),
            value_if_none(self.queued_image.crop_max_y, max_y),
        ]
        context["form"] = PhotoReviewForm(
            queued_image=self.queued_image,
            request=self.request,
            initial={
                "queued_image_id": self.queued_image.id,
                "decision": self.queued_image.decision,
                "x_min": guessed_crop_bounds[0],
                "y_min": guessed_crop_bounds[1],
                "x_max": guessed_crop_bounds[2],
                "y_max": guessed_crop_bounds[3],
                "moderator_why_allowed": self.queued_image.why_allowed,
            },
        )
        context["guessed_crop_bounds"] = guessed_crop_bounds
        context["why_allowed"] = self.queued_image.why_allowed
        context["moderator_why_allowed"] = self.queued_image.why_allowed
        # There are often source links supplied in the justification,
        # and it's convenient to be able to follow them. However, make
        # sure that any maliciously added HTML tags have been stripped
        # before linkifying any URLs:
        context["justification_for_use"] = bleach.linkify(
            bleach.clean(
                self.queued_image.justification_for_use, tags=[], strip=True
            )
        )
        context["google_image_search_url"] = self.get_google_image_search_url(
            person
        )
        context[
            "google_reverse_image_search_url"
        ] = self.get_google_reverse_image_search_url(
            self.queued_image.image.url
        )
        context["person"] = person
        return context

    def form_valid(self, form):
        form.process()
        candidate_link = f'<a href="{self.queued_image.person.get_absolute_url()}">{self.queued_image.person.name}</a>'
        message_mapping = {
            QueuedImage.APPROVED: f"You approved a photo upload for {candidate_link}",
            QueuedImage.REJECTED: f"You rejected a photo upload for {candidate_link}",
            QueuedImage.IGNORE: f"You left a photo upload for {candidate_link} in the queue",
            QueuedImage.UNDECIDED: f"You indicated a photo upload for {candidate_link} should be ignored",
        }
        level_mapping = {QueuedImage.APPROVED: messages.SUCCESS}
        message = message_mapping.get(self.queued_image.decision)
        level = level_mapping.get(self.queued_image.decision, messages.INFO)
        messages.add_message(
            self.request, level, message, extra_tags="safe photo-review"
        )
        return HttpResponseRedirect(reverse("photo-review-list"))

    def form_invalid(self, form):
        return self.render_to_response(
            self.get_context_data(
                queued_image_id=self.queued_image.id, form=form
            )
        )

    def post(self, request, *args, **kwargs):
        self.queued_image = QueuedImage.objects.get(
            pk=kwargs["queued_image_id"]
        )
        form = PhotoReviewForm(
            data=self.request.POST,
            request=request,
            queued_image=self.queued_image,
        )
        if form.is_valid():
            return self.form_valid(form)
        else:
            return self.form_invalid(form)


class SuggestLockView(LoginRequiredMixin, CreateView):
    """This handles creating a SuggestedPostLock from a form submission"""

    model = SuggestedPostLock
    form_class = SuggestedPostLockForm

    def form_invalid(self, form):
        messages.add_message(
            request=self.request,
            level=messages.ERROR,
            message="Cannot add a lock suggestion because candidates are already locked",
            extra_tags="ballot-changed",
        )
        return HttpResponseRedirect(form.instance.ballot.get_absolute_url())

    def form_valid(self, form):
        user = self.request.user
        form.instance.user = user

        LoggedAction.objects.create(
            user=self.request.user,
            action_type=ActionType.SUGGEST_BALLOT_LOCK,
            ballot=form.cleaned_data["ballot"],
            ip_address=get_client_ip(self.request),
            source=form.cleaned_data["justification"],
        )

        messages.add_message(
            self.request,
            messages.SUCCESS,
            message="Thanks for suggesting we lock an area!",
            extra_tags="ballot-changed",
        )

        return super().form_valid(form)

    def get_success_url(self):
        return self.object.ballot.get_absolute_url()


class SuggestLockReviewListView(
    GroupRequiredMixin, LoginRequiredMixin, TemplateView
):
    """
    This is the view which lists all post lock suggestions that need review

    Most people will get to this by clicking on the red highlighted 'Post lock
    suggestions' counter in the header.
    """

    template_name = "moderation_queue/suggestedpostlock_review.html"
    required_group_name = TRUSTED_TO_LOCK_GROUP_NAME

    def get_random_election(self):
        """
        Get a random Election which has ballots with lock suggestions not
        belonging to the user.
        """
        # using annotate and order_by('?') produces strange results
        # see https://code.djangoproject.com/ticket/26390
        # so first do the annotation and filtering
        num_lock_suggestions = Count(
            "ballot",
            filter=Q(ballot__suggestedpostlock__isnull=False)
            & ~Q(ballot__suggestedpostlock__user=self.request.user),
        )
        elections = Election.objects.annotate(
            num_lock_suggestions=num_lock_suggestions
        ).filter(num_lock_suggestions__gte=1)
        # then use that QS to get the QS to randomise and return an object
        return Election.objects.filter(pk__in=elections).order_by("?").first()

    def get_lock_suggestions(self):
        """
        Return a QuerySet of Ballot objects with lock suggestions unrelated to
        the user in the request.
        """
        return (
            Ballot.objects.exclude(candidates_locked=True)
            .exclude(
                Q(suggestedpostlock__isnull=True)
                | Q(suggestedpostlock__user=self.request.user)
            )
            .select_related("election", "post")
            .prefetch_related(
                "officialdocument_set",
                models.Prefetch(
                    "suggestedpostlock_set",
                    SuggestedPostLock.objects.select_related("user"),
                ),
                models.Prefetch(
                    "membership_set",
                    Membership.objects.select_related(
                        "person", "party"
                    ).prefetch_related(
                        "person__other_names", "previous_party_affiliations"
                    ),
                ),
            )
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        ballots = self.get_lock_suggestions()
        election = self.get_random_election()
        context["total_ballots"] = ballots.count()
        context["ballots"] = ballots.filter(election=election)[:10]
        return context


class SOPNReviewRequiredView(ListView):
    """List all post that have a nominations paper, but no lock suggestion"""

    template_name = "moderation_queue/sopn-review-required.html"

    def get(self, *args, **kwargs):
        if "random" in self.request.GET:
            qs = self.get_queryset()
            count = qs.count()
            if count:
                random_offset = random.randrange(count)
                ballot = qs[random_offset]
                url = ballot.get_bulk_add_url()
                return HttpResponseRedirect(url)
        return super().get(*args, **kwargs)

    def get_queryset(self):
        """
        Ballot objects with a document but no lock suggestion
        """
        qs = (
            Ballot.objects.filter(
                suggestedpostlock__isnull=True,
                candidates_locked=False,
                election__current=True,
            )
            .exclude(officialdocument=None)
            .select_related("post", "election")
            .prefetch_related("officialdocument_set")
            .order_by("officialdocument__source_url", "election", "post__label")
        )
        return qs


class PersonNameCleanupView(TemplateView):
    template_name = "moderation_queue/person_name_cleanup.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        people = Person.objects.all().only("name")

        regex = re.compile("[A-Z][A-Z]+")
        context["two_upper"] = [p for p in people if regex.search(p.name)]

        return context


class RemoveSuggestedLocksView(LoginRequiredMixin, GroupRequiredMixin, View):
    required_group_name = TRUSTED_TO_LOCK_GROUP_NAME

    def post(self, request, *args, **kwargs):
        ballot = Ballot.objects.get(ballot_paper_id=request.POST["ballot"])
        ballot.suggestedpostlock_set.all().delete()
        return JsonResponse({"removed": True})
