import mimetypes

import magic
from django import forms
from django.core.exceptions import ValidationError
from django.core.validators import FileExtensionValidator
from official_documents.fields import DropAndPasteFileWidget
from official_documents.models import BallotSOPN, ElectionSOPN
from sopn_parsing.helpers.convert_pdf import (
    PandocConversionError,
    convert_docx_to_pdf,
)


class SOPNUploadFormMixin:
    SUPPORTED_FILE_TYPES = []

    def clean_uploaded_file(self):
        uploaded_file = self.cleaned_data["uploaded_file"]

        mime_type_magic = magic.Magic(mime=True)
        # Only read the first 4kb of the file, for speed but also to prevent
        # funny business with very large files (mime information should always
        # be at the top of the file anyway
        sopn_mimetype = mime_type_magic.from_buffer(uploaded_file.read(4096))
        uploaded_file.seek(0)
        file_type = mimetypes.guess_extension(sopn_mimetype).lstrip(".")

        if file_type not in self.SUPPORTED_FILE_TYPES:
            raise ValidationError(
                f"File type not supported, please upload one of {', '.join(self.SUPPORTED_FILE_TYPES)}"
            )

        # try and convert
        if file_type == "docx":
            try:
                self.cleaned_data["uploaded_file"] = convert_docx_to_pdf(
                    uploaded_file
                )
            except PandocConversionError as e:
                raise forms.ValidationError(
                    f"File is invalid. Please convert to a PDF, JPEG or PNG and retry ({e})"
                )
        return self.cleaned_data["uploaded_file"]


class UploadBallotSOPNForm(SOPNUploadFormMixin, forms.ModelForm):
    SUPPORTED_FILE_TYPES = ["pdf", "docx", "jpeg", "jpg", "png"]

    class Meta:
        model = BallotSOPN
        fields = ("uploaded_file", "source_url", "ballot")

        widgets = {"ballot": forms.HiddenInput()}

    uploaded_file = forms.FileField(
        validators=[
            FileExtensionValidator(allowed_extensions=SUPPORTED_FILE_TYPES)
        ],
        widget=DropAndPasteFileWidget(),
    )


class UploadElectionSOPNForm(SOPNUploadFormMixin, forms.ModelForm):
    SUPPORTED_FILE_TYPES = ["pdf", "docx"]

    class Meta:
        model = ElectionSOPN
        fields = ("uploaded_file", "source_url", "election")

        widgets = {"election": forms.HiddenInput()}

    uploaded_file = forms.FileField(
        validators=[
            FileExtensionValidator(allowed_extensions=SUPPORTED_FILE_TYPES)
        ]
    )
