import cgi

import requests
from candidates.models.db import ActionType, LoggedAction
from candidates.views.version_data import get_change_metadata, get_client_ip
from django import forms
from django.conf import settings
from django.contrib.sites.models import Site
from django.core.exceptions import ValidationError
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.urls import reverse
from moderation_queue.helpers import convert_image_to_png
from people.forms.forms import StrippedCharField
from PIL import Image as PILImage

from .models import CopyrightOptions, QueuedImage, SuggestedPostLock


class UploadPersonPhotoImageForm(forms.ModelForm):
    class Meta:
        model = QueuedImage
        fields = [
            "image",
            "why_allowed",
            "justification_for_use",
            "person",
            "decision",
        ]
        widgets = {
            "person": forms.HiddenInput(),
            "decision": forms.HiddenInput(),
            "why_allowed": forms.RadioSelect(),
            "justification_for_use": forms.Textarea(
                attrs={"rows": 1, "columns": 72},
            ),
        }

    def clean(self):
        cleaned_data = super().clean()
        justification_for_use = cleaned_data.get(
            "justification_for_use", ""
        ).strip()
        why_allowed = cleaned_data.get("why_allowed")
        if why_allowed == "other" and not justification_for_use:
            message = (
                "If you checked 'Other' then you must provide a "
                "justification for why we can use it."
            )
            raise ValidationError(message)
        return cleaned_data

    def save(self, commit):
        """
        Before saving, convert the image to a PNG. This is done while
        the image is still an InMemoryUpload object
        """
        png_image = convert_image_to_png(self.instance.image.file)
        filename = self.instance.image.name
        extension = filename.split(".")[-1]
        filename = filename.replace(extension, "png")
        self.instance.image.save(filename, png_image, save=commit)
        return super().save(commit=commit)


class UploadPersonPhotoURLForm(forms.Form):
    image_url = StrippedCharField(widget=forms.URLInput())
    why_allowed_url = forms.ChoiceField(
        choices=CopyrightOptions.WHY_ALLOWED_CHOICES, widget=forms.RadioSelect()
    )
    justification_for_use_url = StrippedCharField(
        widget=forms.Textarea(attrs={"rows": 1, "columns": 72}), required=False
    )

    def clean_image_url(self):
        image_url = self.cleaned_data["image_url"]
        # At least do a HEAD request to check that the Content-Type
        # looks reasonable:
        response = requests.head(image_url, allow_redirects=True)
        if (400 <= response.status_code < 500) or (
            500 <= response.status_code < 600
        ):
            msg = "That URL produced an HTTP error status code: {0}"
            raise ValidationError(msg.format(response.status_code))
        content_type = response.headers["content-type"]
        main, sub = cgi.parse_header(content_type)
        if not main.startswith("image/"):
            msg = "This URL isn't for an image - it had Content-Type: {0}"
            raise ValidationError(msg.format(main))
        return image_url


class PhotoRotateForm(forms.Form):
    def __init__(self, *args, **kwargs):
        self.queued_image = kwargs.pop("queued_image")
        self.request = kwargs.pop("request")
        super().__init__(*args, **kwargs)

    def clean(self):
        return super().clean()

    def process(self):
        if "rotate_left" in self.request._post:
            rotation_direction = "left"
            self.rotate_photo(self.queued_image.id, rotation_direction)
        elif "rotate_right" in self.request._post:
            rotation_direction = "right"
            self.rotate_photo(self.queued_image.id, rotation_direction)
        else:
            raise Exception("No rotation direction specified")

    def rotate_photo(self, queued_image_id, rotation_direction):
        queued_image = QueuedImage.objects.get(id=queued_image_id)
        image_path = queued_image.image.path
        image = PILImage.open(queued_image.image)
        if rotation_direction == "left":
            rotated = image.rotate(90, expand=True)
        elif rotation_direction == "right":
            rotated = image.rotate(-90, expand=True)
        rotated.save(image_path, "PNG")
        return rotated


class PhotoReviewForm(forms.Form):
    def __init__(self, *args, **kwargs):
        self.queued_image = kwargs.pop("queued_image")
        self.request = kwargs.pop("request")
        super().__init__(*args, **kwargs)

    queued_image_id = forms.IntegerField(
        required=True, widget=forms.HiddenInput()
    )
    x_min = forms.IntegerField(min_value=0)
    x_max = forms.IntegerField(min_value=1)
    y_min = forms.IntegerField(min_value=0)
    y_max = forms.IntegerField(min_value=1)
    decision = forms.ChoiceField(
        choices=QueuedImage.DECISION_CHOICES, widget=forms.widgets.RadioSelect
    )
    rejection_reason = forms.CharField(widget=forms.Textarea(), required=False)
    justification_for_use = forms.CharField(
        widget=forms.Textarea(), required=False
    )
    moderator_why_allowed = forms.ChoiceField(
        choices=CopyrightOptions.WHY_ALLOWED_CHOICES,
        widget=forms.widgets.RadioSelect,
    )

    def process(self):
        action_method = getattr(self, self.cleaned_data["decision"])
        action_method()

    def create_logged_action(self, version_id=""):
        action_types = {
            QueuedImage.APPROVED: ActionType.PHOTO_APPROVE,
            QueuedImage.REJECTED: ActionType.PHOTO_REJECT,
            QueuedImage.IGNORE: ActionType.PHOTO_IGNORE,
        }
        LoggedAction.objects.create(
            user=self.request.user,
            action_type=action_types[self.cleaned_data["decision"]],
            ip_address=get_client_ip(self.request),
            popit_person_new_version=version_id,
            person=self.queued_image.person,
            source=self.update_message,
        )

    @property
    def update_message(self):
        messages = {
            QueuedImage.APPROVED: f'Approved a photo upload from {self.queued_image.uploaded_by} who provided the message: "{self.queued_image.justification_for_use}"',
            QueuedImage.REJECTED: f"Rejected a photo upload from {self.queued_image.uploaded_by}",
            QueuedImage.IGNORE: f"Ignored a photo upload from {self.queued_image.uploaded_by} (This usually means it was a duplicate)",
        }
        return messages[self.cleaned_data["decision"]]

    def approved(self):
        self.queued_image.decision = self.cleaned_data["decision"]
        self.queued_image.crop_min_x = self.cleaned_data["x_min"]
        self.queued_image.crop_min_y = self.cleaned_data["y_min"]
        self.queued_image.crop_max_x = self.cleaned_data["x_max"]
        self.queued_image.crop_max_y = self.cleaned_data["y_max"]
        self.queued_image.save()
        self.queued_image.person.create_person_image(
            queued_image=self.queued_image,
            copyright=self.cleaned_data["moderator_why_allowed"],
        )
        change_metadata = get_change_metadata(self.request, self.update_message)
        self.queued_image.person.record_version(change_metadata)
        self.queued_image.person.save()
        self.create_logged_action(version_id=change_metadata["version_id"])

        candidate_full_url = self.request.build_absolute_uri(
            self.queued_image.person.get_absolute_url(self.request)
        )
        site_name = Site.objects.get_current().name
        subject = f"{site_name} image upload approved"
        self.send_mail(
            subject=subject,
            template_name="moderation_queue/photo_approved_email.txt",
            context={
                "site_name": site_name,
                "candidate_page_url": candidate_full_url,
                "intro": (
                    "Thank you for submitting a photo to "
                    f"{site_name}. It has been uploaded to "
                    "the candidate page here:"
                ),
                "signoff": f"Many thanks from the {site_name} volunteers",
            },
        )

    def rejected(self):
        self.queued_image.decision = self.cleaned_data["decision"]
        self.queued_image.save()
        self.create_logged_action()
        retry_upload_link = self.request.build_absolute_uri(
            reverse(
                "photo-upload",
                kwargs={"person_id": self.queued_image.person.id},
            )
        )
        site_name = Site.objects.get_current().name
        photo_review_url = self.request.build_absolute_uri(
            self.queued_image.get_absolute_url()
        )
        self.send_mail(
            subject=f"{site_name} image moderation results",
            template_name="moderation_queue/photo_rejected_email.txt",
            context={
                "reason": self.cleaned_data["rejection_reason"],
                "retry_upload_link": retry_upload_link,
                "photo_review_url": photo_review_url,
                "intro": (
                    "Thank-you for uploading a photo of "
                    f"{self.queued_image.person.name} to {site_name}, "
                    "but unfortunately we can't use that image because:"
                ),
                "possible_actions": (
                    "You can just reply to this email if you want to "
                    "discuss that further, or you can try uploading a "
                    "photo with a different reason or justification "
                    "for its use using this link:"
                ),
                "signoff": (f"Many thanks from the {site_name} volunteers"),
            },
            email_support_too=True,
        )

    def ignore(self):
        self.queued_image.decision = self.cleaned_data["decision"]
        self.queued_image.save()
        self.create_logged_action()

    def undecided(self):
        self.queued_image.decision = self.cleaned_data["decision"]
        self.queued_image.save()

    def send_mail(
        self, subject, template_name, context, email_support_too=False
    ):
        if not self.queued_image.user:
            # We can't send emails to bots…yet.
            return

        message = render_to_string(template_name=template_name, context=context)
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


class SuggestedPostLockForm(forms.ModelForm):
    class Meta:
        model = SuggestedPostLock
        fields = ["justification", "ballot"]
        widgets = {
            "ballot": forms.HiddenInput(),
            "justification": forms.Textarea(attrs={"rows": 1, "columns": 72}),
        }

    def clean(self):
        ballot = self.cleaned_data["ballot"]
        if ballot.candidates_locked:
            raise ValidationError(
                "Cannot create a lock suggestion for a locked ballot"
            )
        return self.cleaned_data
