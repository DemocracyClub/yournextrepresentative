from io import BytesIO
from tempfile import NamedTemporaryFile

import requests
from PIL import Image as PillowImage

# 15MB — Rekognition's S3 object size limit
MAX_IMAGE_BYTES = 15 * 1024 * 1024


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
    converted = photo.copy().convert("RGB")
    w, h = converted.size

    # Render at full size first; return immediately if already within the limit.
    bytes_obj = BytesIO()
    converted.save(bytes_obj, "PNG")
    if bytes_obj.tell() <= MAX_IMAGE_BYTES:
        return bytes_obj

    # Binary search over scale factors (0–1) to find the largest image that
    # still encodes to <= MAX_IMAGE_BYTES.
    lo, hi = 0.0, 1.0
    best = bytes_obj  # fallback; always replaced within a couple of iterations
    for _ in range(20):
        mid = (lo + hi) / 2
        resized = converted.resize(
            (max(1, int(w * mid)), max(1, int(h * mid))), PillowImage.LANCZOS
        )
        buf = BytesIO()
        resized.save(buf, "PNG")
        if buf.tell() <= MAX_IMAGE_BYTES:
            lo = mid  # this scale fits — search higher
            best = buf
        else:
            hi = mid  # too large — search lower
    return best


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
