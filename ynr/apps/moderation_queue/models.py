from datetime import date
from os.path import join, splitext
import uuid

from django.contrib.auth.models import User
from django.db import models
from django.urls import reverse


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
