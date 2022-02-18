import cgi

import requests
from django import forms
from django.conf import settings
from django.core.mail import send_mail
from django.core.exceptions import ValidationError
from django.contrib.sites.models import Site
from django.template.loader import render_to_string
from candidates.models.db import ActionType, LoggedAction
from candidates.views.version_data import get_change_metadata, get_client_ip

from people.forms.forms import StrippedCharField

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
                attrs={"rows": 1, "columns": 72}
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

    def create_logged_action(self, action_type, update_message, version_id=""):
        LoggedAction.objects.create(
            user=self.request.user,
            action_type=action_type,
            ip_address=get_client_ip(self.request),
            popit_person_new_version=version_id,
            person=self.queued_image.person,
            source=update_message,
        )

    def approved(self):
        self.queued_image.decision = QueuedImage.APPROVED
        self.queued_image.crop_min_x = self.cleaned_data["x_min"]
        self.queued_image.crop_min_y = self.cleaned_data["y_min"]
        self.queued_image.crop_max_x = self.cleaned_data["x_max"]
        self.queued_image.crop_max_y = self.cleaned_data["y_max"]
        self.queued_image.save()
        self.queued_image.person.create_person_image(
            queued_image=self.queued_image,
            copyright=self.cleaned_data["moderator_why_allowed"],
        )
        sentence = "Approved a photo upload from {uploading_user}"
        ' who provided the message: "{message}"'

        update_message = sentence.format(
            uploading_user=self.queued_image.uploaded_by,
            message=self.queued_image.justification_for_use,
        )
        change_metadata = get_change_metadata(self.request, update_message)
        self.queued_image.person.record_version(change_metadata)
        self.queued_image.person.save()
        self.create_logged_action(
            action_type=ActionType.PHOTO_APPROVE,
            update_message=update_message,
            version_id=change_metadata["version_id"],
        )

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
