import ast
import json
import uuid
from datetime import date
from os.path import join, splitext
from tempfile import NamedTemporaryFile

import sorl.thumbnail
from django.contrib.auth.models import User
from django.db import models
from django.urls import reverse
from PIL import Image as PillowImage
from PIL import ImageOps

from .helpers import convert_image_to_png

PHOTO_REVIEWERS_GROUP_NAME = "Photo Reviewers"
VERY_TRUSTED_USER_GROUP_NAME = "Very Trusted User"


class CopyrightOptions:
    PUBLIC_DOMAIN = "public-domain"
    COPYRIGHT_ASSIGNED = "copyright-assigned"
    PROFILE_PHOTO = "profile-photo"
    OTHER = "other"

    WHY_ALLOWED_CHOICES = (
        (
            PUBLIC_DOMAIN,
            "This photograph is free of any copyright restrictions",
        ),
        (
            COPYRIGHT_ASSIGNED,
            (
                "I own copyright of this photo and I assign the copyright "
                "to Democracy Club in return for it being displayed "
                "on this site."
            ),
        ),
        (
            PROFILE_PHOTO,
            (
                "This is the candidate's public profile photo from social "
                "media (e.g. Twitter, Facebook) or their official campaign "
                "page"
            ),
        ),
        (OTHER, "Other"),
    )


def queued_image_filename(queued_image_instance, filename):
    original_extension = splitext(filename)[1]
    base_filename = "{0}-{1}".format(
        queued_image_instance.person_id, uuid.uuid4()
    )
    if original_extension:
        base_filename += original_extension
    return join(date.today().strftime("queued-images/%Y/%m/%d"), base_filename)


class QueuedImage(models.Model):
    APPROVED = "approved"
    REJECTED = "rejected"
    UNDECIDED = "undecided"
    IGNORE = "ignore"

    DECISION_CHOICES = (
        (APPROVED, "Approved"),
        (REJECTED, "Rejected"),
        (UNDECIDED, "Undecided"),
        (IGNORE, "Ignore"),
    )

    why_allowed = models.CharField(
        max_length=64,
        choices=CopyrightOptions.WHY_ALLOWED_CHOICES,
        default=CopyrightOptions.OTHER,
    )
    justification_for_use = models.TextField(blank=True)
    decision = models.CharField(
        max_length=32, choices=DECISION_CHOICES, default=UNDECIDED
    )
    image = models.ImageField(upload_to=queued_image_filename, max_length=512)
    person = models.ForeignKey(
        "people.Person", blank=True, null=True, on_delete=models.CASCADE
    )
    user = models.ForeignKey(
        User, blank=True, null=True, on_delete=models.CASCADE
    )

    crop_min_x = models.PositiveIntegerField(blank=True, null=True)
    crop_min_y = models.PositiveIntegerField(blank=True, null=True)
    crop_max_x = models.PositiveIntegerField(blank=True, null=True)
    crop_max_y = models.PositiveIntegerField(blank=True, null=True)

    detection_metadata = models.TextField(blank=True)

    face_detection_tried = models.BooleanField(default=False)
    rotation_tried = models.BooleanField(default=False)

    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    def __str__(self):
        message = "Image uploaded by {user} of candidate {person_id}"
        return message.format(
            user=self.user, person_id=(self.person.id if self.person else None)
        )

    def get_absolute_url(self):
        return reverse("photo-review", kwargs={"queued_image_id": self.id})

    @property
    def crop_fields(self):
        return ["crop_min_x", "crop_min_y", "crop_max_x", "crop_max_y"]

    @property
    def has_crop_bounds(self):
        return not any(getattr(self, c) is None for c in self.crop_fields)

    @property
    def crop_bounds(self):
        if not self.has_crop_bounds:
            return []
        return [getattr(self, field) for field in self.crop_fields]

    @property
    def uploaded_by(self):
        if self.user:
            return self.user.username
        return "a robot 🤖"

    def start_image_processing(self):
        from django_q.tasks import async_chain

        async_chain(
            [
                (
                    "moderation_queue.tasks.normalise_queued_image",
                    (self.id,),
                ),
                (
                    "moderation_queue.tasks.detect_faces_for_queued_image",
                    (self.id,),
                ),
            ]
        )

    def normalise_image(self):
        pil_img = PillowImage.open(self.image.file)
        pil_img = ImageOps.exif_transpose(pil_img)
        png_buffer = convert_image_to_png(pil_img)
        self.image.save(self.image.name, png_buffer, save=False)
        sorl.thumbnail.delete(self.image.name, delete_file=False)

    def _face_crop_bound(self, bound, im_size, scaling_factor):
        return max(0, bound * im_size * scaling_factor)

    def _apply_face_detection(self, detected):
        if not (detected and detected.get("FaceDetails")):
            return
        # AWS crops faces tightly by default. these scaling factors give a
        # slightly wider crop that includes more context around the face.
        MIN_SCALING_FACTOR = 0.7
        MAX_SCALING_FACTOR = 1.3
        bb = detected["FaceDetails"][0]["BoundingBox"]
        self.crop_min_x = self._face_crop_bound(
            bb["Left"], self.image.width, MIN_SCALING_FACTOR
        )
        self.crop_min_y = self._face_crop_bound(
            bb["Top"], self.image.height, MIN_SCALING_FACTOR
        )
        self.crop_max_x = self._face_crop_bound(
            bb["Width"], self.image.width, MAX_SCALING_FACTOR
        )
        self.crop_max_y = self._face_crop_bound(
            bb["Height"], self.image.height, MAX_SCALING_FACTOR
        )
        self.detection_metadata = json.dumps(detected, indent=4)

    def detect_faces(self):
        import boto3

        try:
            from storages.backends.s3 import S3Storage
        except ImportError:
            S3Storage = None

        try:
            rekognition = boto3.client("rekognition", region_name="eu-west-1")
            storage = self.image.storage
            if S3Storage and isinstance(storage, S3Storage):
                rekognition_image = {
                    "S3Object": {
                        "Bucket": storage.bucket_name,
                        "Name": storage._normalize_name(self.image.name),
                    }
                }
            else:
                with self.image.open("rb") as f:
                    rekognition_image = {"Bytes": f.read()}
            detected = rekognition.detect_faces(
                Image=rekognition_image, Attributes=["ALL"]
            )
            self._apply_face_detection(detected)
        finally:
            self.face_detection_tried = True
            self.rotation_tried = True
            self.save()

    def crop_image(self):
        """
        Returns a temporary file containing the cropped image
        """
        original = PillowImage.open(self.image.file)
        cropped = original.crop(self.crop_bounds)
        ntf = NamedTemporaryFile(delete=False)
        cropped.save(ntf.name, "PNG")
        return ntf

    @property
    def facial_detection(self):
        if self.detection_metadata:
            self.detection_metadata = ast.literal_eval(self.detection_metadata)
            return self.detection_metadata
        return {}


class SuggestedPostLock(models.Model):
    ballot = models.ForeignKey("candidates.Ballot", on_delete=models.CASCADE)
    user = models.ForeignKey(
        User, blank=False, null=False, on_delete=models.CASCADE
    )
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)
    justification = models.TextField(
        blank=True,
        help_text="e.g I've reviewed the nomination paper for this area",
    )
    ballot_hash = models.CharField(max_length=255)

    def save(self, *args, **kwargs):
        """
        On creation, stores the hashed membership of the related ballot. This
        allows us to detect out of date lock suggestions based on the hash.
        """
        if not self.pk:
            self.ballot_hash = self.ballot.hashed_memberships
        return super().save(*args, **kwargs)
