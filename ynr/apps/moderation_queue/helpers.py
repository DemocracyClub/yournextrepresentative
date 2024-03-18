from io import BytesIO
from tempfile import NamedTemporaryFile

import requests
from candidates.models.db import ActionType, LoggedAction
from candidates.views.version_data import get_client_ip
from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.urls import reverse
from PIL import ExifTags, ImageOps
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


def rotate_photo(original_image):
    # TO DO issue #2026 : This does not handle URL
    # uploads.

    # If an image has an EXIF Orientation tag, other than 1,
    # return a new image that is transposed accordingly.
    # The new image will have the orientation data removed.
    # https://pillow.readthedocs.io/en/stable/_modules/PIL/ImageOps.html#exif_transpose
    # Otherwise, return a copy of the image. If an image
    # has an EXIF Orientation tag of 1, it might still
    # need to be rotated, but we can handle that manually
    # in the review process.
    pil_image = PillowImage.open(original_image)

    for orientation in ExifTags.TAGS:
        if ExifTags.TAGS[orientation] == "Orientation":
            break
        exif = pil_image.getexif()
        if exif and exif.get(274):
            pil_image = ImageOps.exif_transpose(pil_image)
        buffer = BytesIO()
        try:
            pil_image.save(buffer, "PNG")
        except AttributeError as e:
            print(f"An error occurred: {e}")
            continue
    return pil_image


def resize_photo(photo, original_image):
    if not isinstance(photo, PillowImage.Image):
        pil_image = PillowImage.open(photo)
    else:
        pil_image = photo

    if original_image.width > 5000 or original_image.height > 5000:
        size = 2000, 2000
        pil_image.thumbnail(size)
        buffer = BytesIO()
        pil_image.save(buffer, "PNG")
        return pil_image
    return photo


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
        photo = PillowImage.open(photo)
    converted = photo.convert("RGBA")
    bytes_obj = BytesIO()
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
