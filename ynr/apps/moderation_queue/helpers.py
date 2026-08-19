from io import BytesIO
from tempfile import NamedTemporaryFile
from typing import Optional, Tuple

import requests
from PIL import Image as PillowImage
from PIL import ImageOps

# 15MB — Rekognition's S3 object size limit
MAX_IMAGE_BYTES = 15 * 1024 * 1024


def strip_alpha(photo):
    if photo.mode in ("RGBA", "LA") or (
        photo.mode == "P" and "transparency" in photo.info
    ):
        background = PillowImage.new("RGB", photo.size, (255, 255, 255))
        alpha_img = photo.convert("RGBA")
        background.paste(alpha_img, mask=alpha_img.getchannel("A"))
        alpha_img.close()
        return background

    return photo.convert("RGB")


def save_png_to_bytes(photo):
    buf = BytesIO()
    photo.save(buf, "PNG", optimize=True)
    size = buf.tell()
    buf.seek(0)
    return buf, size


def strip_exifdata(photo):
    photo.info.pop("exif", None)
    photo.info.pop("icc_profile", None)
    photo.info.pop("xmp", None)
    photo.info.pop("XML:com.adobe.xmp", None)
    return photo


def check_png_size(photo) -> Tuple[Optional[BytesIO], int]:
    """
    Encode `photo` as PNG.

    If the size is below MAX_IMAGE_BYTES then return the BytesIO buffer,
    otherwise delete the in-memory object.

    """
    buf = BytesIO()
    photo.save(buf, "PNG")
    size = buf.tell()

    if size <= MAX_IMAGE_BYTES:
        buf.seek(0)
        return buf, size

    buf.close()
    return None, size


def convert_image_to_png(photo):
    # If the photo is not already a PillowImage object
    # coming from the form, then we need to
    # open it as a PillowImage object before
    # converting it to RGBA.
    if not isinstance(photo, PillowImage.Image):
        photo = PillowImage.open(photo)

    photo = ImageOps.exif_transpose(photo)
    photo = strip_alpha(photo)
    photo = strip_exifdata(photo)

    w, h = photo.size

    # Render at full size first; return immediately if already within the limit.
    # Try full-size first.
    png_image, size = check_png_size(photo)
    if png_image:
        return png_image

    # Binary search over scale factors (0–1) to find the largest image that
    # still encodes to <= MAX_IMAGE_BYTES.
    lo, hi = 0.0, 1.0
    best = None

    for _ in range(12):
        mid = (lo + hi) / 2

        resized = photo.resize(
            (max(1, int(w * mid)), max(1, int(h * mid))),
            PillowImage.Resampling.LANCZOS,
        )

        try:
            png_image, size = check_png_size(resized)
        finally:
            resized.close()

        if png_image is not None:
            lo = mid  # it fits, try larger

            if best is not None:
                best.close()

            best = png_image
        else:
            hi = mid  # too large, try smaller

    if best is not None:
        best.seek(0)
        return best

    # Worst case: the above has failed to find anything so we just
    # resize the image to _something_. This is likely too lossy, but
    # it's a failsafe to get some sort of image.
    small = photo.thumbnail(
        (800, 800),
        PillowImage.Resampling.LANCZOS,
    )
    try:
        buf, _ = check_png_size(small)
        return buf
    finally:
        small.close()


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
