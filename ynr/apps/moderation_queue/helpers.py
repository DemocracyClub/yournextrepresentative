from django.http import HttpResponseRedirect
from django.urls import reverse
from candidates.models.db import ActionType, LoggedAction
from candidates.views.version_data import get_client_ip
from .models import QueuedImage
from django.shortcuts import render


def upload_photo_response(request, person, image_form, url_form):
    return render(
        request,
        "moderation_queue/photo-upload-new.html",
        {
            "image_form": image_form,
            "url_form": url_form,
            "queued_images": QueuedImage.objects.filter(
                person=person, decision="undecided"
            ).order_by("created"),
            "person": person,
        },
    )


def image_form_valid_response(request, person, image_form):
    # Make sure that we save the user that made the upload
    queued_image = image_form.save(commit=False)
    queued_image.user = request.user
    queued_image.save()
    # Record that action:
    LoggedAction.objects.create(
        user=request.user,
        action_type=ActionType.PHOTO_UPLOAD,
        ip_address=get_client_ip(request),
        popit_person_new_version="",
        person=person,
        source=image_form.cleaned_data["justification_for_use"],
    )
    return HttpResponseRedirect(
        reverse("photo-upload-success", kwargs={"person_id": person.id})
    )
