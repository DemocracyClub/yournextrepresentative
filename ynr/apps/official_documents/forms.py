from django import forms
from django.core.validators import FileExtensionValidator
from official_documents.models import BallotSOPN, ElectionSOPN
from sopn_parsing.helpers.convert_pdf import (
    PandocConversionError,
    convert_sopn_to_pdf,
)


class UploadBallotSOPNForm(forms.ModelForm):
    class Meta:
        model = BallotSOPN
        fields = ("uploaded_file", "source_url", "ballot")

        widgets = {"ballot": forms.HiddenInput()}

    uploaded_file = forms.FileField(
        validators=[FileExtensionValidator(allowed_extensions=["pdf", "docx"])]
    )

    def clean_uploaded_file(self):
        uploaded_file = self.cleaned_data["uploaded_file"]
        # try and convert
        try:
            self.cleaned_data["uploaded_file"] = convert_sopn_to_pdf(
                uploaded_file
            )
        except PandocConversionError:
            raise forms.ValidationError(
                "File is invalid. Please convert to a PDF and retry"
            )
        return self.cleaned_data["uploaded_file"]


class UploadElectionSOPNForm(forms.ModelForm):
    class Meta:
        model = ElectionSOPN
        fields = ("uploaded_file", "source_url", "election")

        widgets = {"election": forms.HiddenInput()}

    uploaded_file = forms.FileField(
        validators=[FileExtensionValidator(allowed_extensions=["pdf", "docx"])]
    )

    def clean_uploaded_file(self):
        uploaded_file = self.cleaned_data["uploaded_file"]
        # try and convert
        try:
            self.cleaned_data["uploaded_file"] = convert_sopn_to_pdf(
                uploaded_file
            )
        except PandocConversionError:
            raise forms.ValidationError(
                "File is invalid. Please convert to a PDF and retry"
            )
        return self.cleaned_data["uploaded_file"]
