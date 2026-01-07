from io import BytesIO
from tempfile import NamedTemporaryFile

import requests
from candidates.models.db import ActionType, LoggedAction
from candidates.views.version_data import get_change_metadata, get_client_ip
from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.urls import reverse
from PIL import Image as PillowImage

from .models import QueuedImage


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
    # TODO: Record this action and update the person versions.
    # this needs a separate path than the usual record_version
    change_metadata = get_change_metadata(
        request, information_source=image_form.cleaned_data["why_allowed"]
    )
    change_metadata.update({"photo-upload": True})

    person.record_version(change_metadata)
    person.save()

    LoggedAction.objects.create(
        user=request.user,
        action_type=ActionType.PHOTO_UPLOAD,
        ip_address=get_client_ip(request),
        popit_person_new_version="",
        person=person,
        source=image_form.cleaned_data["why_allowed"],
    )
    return HttpResponseRedirect(
        reverse("photo-upload-success", kwargs={"person_id": person.id})
    )


def convert_image_to_png(photo):
    # Some uploaded images are CYMK, which gives you an error when
    # you try to write them as PNG, so convert to RGBA (this is
    # RGBA rather than RGB so that any alpha channel (transparency)
    # is preserved).

    # If the photo is not already a PillowImage object
    # coming from the form, then we need to
    # open it as a PillowImage object before
    # converting it to RGBA.
    if not isinstance(photo, PillowImage.Image):
        photo = PillowImage.open(photo).convert("RGBA")
    else:
        photo = photo.convert("RGBA")
    bytes_obj = BytesIO()
    converted = photo.copy()
    converted = converted.convert("RGB")
    converted.save(bytes_obj, "PNG")
    return bytes_obj


class ImageDownloadException(Exception):
    pass


def download_image_from_url(image_url, max_size_bytes=(50 * 2**20)):
    """This downloads an image to a temporary file and returns the filename

    It raises an ImageDownloadException if a GET for the URL results
    in a HTTP response with status code other than 200, or the
    downloaded resource doesn't seem to be an image. It's the
    responsibility of the caller to delete the image once they're
    finished with it.  If the download exceeds max_size_bytes (default
    50MB) then this will also throw an ImageDownloadException."""
    with NamedTemporaryFile(delete=True) as image_ntf:
        image_response = requests.get(image_url, stream=True)
        if image_response.status_code != 200:
            msg = (
                "  Ignoring an image URL with non-200 status code "
                "({status_code}): {url}"
            )
            raise ImageDownloadException(
                msg.format(
                    status_code=image_response.status_code, url=image_url
                )
            )
        # Download no more than a megabyte at a time:
        downloaded_so_far = 0
        for chunk in image_response.iter_content(chunk_size=(2 * 20)):
            downloaded_so_far += len(chunk)
            if downloaded_so_far > max_size_bytes:
                raise ImageDownloadException(
                    "The image exceeded the maximum allowed size"
                )
            image_ntf.write(chunk)

        return convert_image_to_png(image_ntf.file)
