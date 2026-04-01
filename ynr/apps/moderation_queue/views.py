import random
import re
from typing import Any, Dict
from urllib.parse import quote

import nh3
from auth_helpers.views import GroupRequiredMixin
from candidates.models import TRUSTED_TO_LOCK_GROUP_NAME, Ballot, LoggedAction
from candidates.models.db import ActionType
from candidates.views.version_data import get_client_ip
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.paginator import Paginator
from django.db import models
from django.db.models import Exists, OuterRef, Q
from django.http import (
    Http404,
    HttpResponseBadRequest,
    HttpResponseRedirect,
    JsonResponse,
)
from django.shortcuts import get_object_or_404
from django.urls import reverse
from django.utils.html import urlize
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.generic import (
    ListView,
    TemplateView,
    View,
)
from elections.models import Election
from moderation_queue.filters import QueuedImageFilter
from moderation_queue.helpers import (
    ImageDownloadException,
    download_image_from_url,
    image_form_valid_response,
    upload_photo_response,
)
from people.models import TRUSTED_TO_EDIT_NAME, EditLimitationStatuses, Person
from popolo.models import Membership, OtherName

from .forms import (
    PhotoReviewForm,
    PhotoRotateForm,
    SuggestedPostLockForm,
    UploadPersonPhotoImageForm,
    UploadPersonPhotoURLForm,
)
from .models import PHOTO_REVIEWERS_GROUP_NAME, QueuedImage, SuggestedPostLock


@login_required
def upload_photo(request, person_id):
    person = get_object_or_404(Person, id=person_id)
    if person.edit_limitations == EditLimitationStatuses.EDITS_PREVENTED.name:
        raise Http404()
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
        context["object_list"] = Paginator(filter_obj.qs, 20).page(1)
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
        url = "https://lens.google.com/uploadbyurl?url="
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
        # before linkifying any URLs:.
        context["justification_for_use"] = urlize(
            nh3.clean(self.queued_image.justification_for_use, tags={"a"})
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
        self.queued_image = self.form.process()
        if isinstance(form, PhotoReviewForm):
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
        return HttpResponseRedirect(
            reverse(
                "photo-review",
                kwargs={"queued_image_id": self.queued_image.id},
            )
        )

    def form_invalid(self, form):
        return self.render_to_response(self.get_context_data(form=form))

    def post(self, request, *args, **kwargs):
        self.queued_image = QueuedImage.objects.get(
            pk=kwargs["queued_image_id"]
        )
        if "rotate" in request.POST:
            self.form = PhotoRotateForm(
                data=self.request.POST,
                request=request,
                queued_image=self.queued_image,
            )
        else:
            self.form = PhotoReviewForm(
                data=self.request.POST,
                request=request,
                queued_image=self.queued_image,
            )
        if self.form.is_valid():
            return self.form_valid(self.form)
        return self.form_invalid(self.form)


class SuggestLockView(LoginRequiredMixin, TemplateView):
    """Review lock suggestions for a single ballot."""

    template_name = "moderation_queue/suggestedpostlock_review_ballot.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["ballot"] = get_object_or_404(
            Ballot.objects.select_related("election", "post")
            .prefetch_related(
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
            .annotate(
                current_user_suggested_lock=Exists(
                    SuggestedPostLock.objects.filter(
                        ballot=OuterRef("pk"),
                        user=self.request.user,
                    )
                )
            ),
            ballot_paper_id=self.kwargs["ballot_paper_id"],
        )
        return context


class SuggestLockCreateView(LoginRequiredMixin, View):
    """Accept a POST to create a SuggestedPostLock, then redirect."""

    def post(self, request, ballot_paper_id):
        ballot = get_object_or_404(Ballot, ballot_paper_id=ballot_paper_id)
        form = SuggestedPostLockForm(request.POST, ballot=ballot)

        if not form.is_valid():
            messages.add_message(
                request=request,
                level=messages.ERROR,
                message="Cannot add a lock suggestion because candidates are already locked",
                extra_tags="ballot-changed",
            )
            return HttpResponseRedirect(ballot.get_absolute_url())

        justification = form.cleaned_data["justification"]
        SuggestedPostLock.objects.create(
            ballot=ballot,
            user=request.user,
            justification=justification,
        )
        LoggedAction.objects.create(
            user=request.user,
            action_type=ActionType.SUGGEST_BALLOT_LOCK,
            ballot=ballot,
            ip_address=get_client_ip(request),
            source=justification,
        )
        messages.add_message(
            request,
            messages.SUCCESS,
            message="Thanks for suggesting we lock an area!",
            extra_tags="ballot-changed",
        )

        next_url = request.GET.get("next")
        if next_url and url_has_allowed_host_and_scheme(
            next_url, allowed_hosts={request.get_host()}
        ):
            return HttpResponseRedirect(next_url)
        return HttpResponseRedirect(ballot.get_absolute_url())


class BaseLockSuggestionMixin:
    required_group_name = TRUSTED_TO_LOCK_GROUP_NAME

    def get_queryset(self):
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
            .select_related("election", "post", "sopn")
            .prefetch_related(
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
            .annotate(
                current_user_suggested_lock=Exists(
                    SuggestedPostLock.objects.filter(
                        ballot=OuterRef("pk"),
                        user=self.request.user,
                    )
                )
            )
        )


class SuggestLockReviewListView(
    BaseLockSuggestionMixin,
    GroupRequiredMixin,
    LoginRequiredMixin,
    TemplateView,
):
    """
    This is the view which lists all post lock suggestions that need review

    Most people will get to this by clicking on the red highlighted 'Post lock
    suggestions' counter in the header.
    """

    template_name = "moderation_queue/suggestedpostlock_review.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        ballots = self.get_queryset()
        context["total_ballots"] = ballots.count()
        election_ids = ballots.values_list("election_id", flat=True).distinct()
        election = (
            Election.objects.filter(pk__in=election_ids).order_by("?").first()
        )
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
        return (
            Ballot.objects.filter(
                suggestedpostlock__isnull=True,
                candidates_locked=False,
                election__current=True,
            )
            .exclude(sopn=None)
            .select_related("post", "election", "sopn")
            .order_by("election", "post__label")
        )


class PersonNameCleanupView(TemplateView):
    template_name = "moderation_queue/person_name_cleanup.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        people = Person.objects.all().only("name")

        regex = re.compile("[A-Z][A-Z]+")
        context["two_upper"] = [p for p in people if regex.search(p.name)]

        return context


class PersonNameEditReviewListView(GroupRequiredMixin, ListView):
    http_method_names = ["get", "post"]
    template_name = "moderation_queue/person_name_review.html"
    required_group_name = TRUSTED_TO_EDIT_NAME
    model = OtherName

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        object_list = OtherName.objects.filter(needs_review=True)
        context = super().get_context_data(**kwargs)
        context["object_list"] = object_list

        return context

    def post(self, request, **kwargs):
        other_name = OtherName.objects.get(pk=request.POST.get("other_name_pk"))

        if "decision_approve" in request.POST:
            self.approve_name_change(other_name)
        elif "decision_reject" in request.POST:
            self.reject_name_change(other_name)
        elif "decision_delete" in request.POST:
            self.delete_name_change(other_name)

        else:
            raise ValueError("Invalid decision")
        return HttpResponseRedirect(reverse("person-name-review"))

    def approve_name_change(self, other_name):
        person = other_name.content_object
        person.edit_name(
            suggested_name=other_name.name,
            initial_name=person.name,
            user=self.request.user,
        )
        person.save()
        # Note: We don't need to explicitly send a notification here
        # it will be handled in person.edit_name()

    def delete_name_change(self, other_name):
        other_name.delete()

    def reject_name_change(self, other_name):
        other_name.needs_review = False
        other_name.save()


class RemoveSuggestedLocksView(LoginRequiredMixin, GroupRequiredMixin, View):
    required_group_name = TRUSTED_TO_LOCK_GROUP_NAME

    def post(self, request, *args, **kwargs):
        ballot = Ballot.objects.get(ballot_paper_id=request.POST["ballot"])
        ballot.suggestedpostlock_set.all().delete()
        if request.headers.get("x-requested-with") == "XMLHttpRequest":
            return JsonResponse({"removed": True})
        return HttpResponseRedirect(ballot.get_absolute_url())
