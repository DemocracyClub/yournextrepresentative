from django import forms

from sopn_parsing.helpers.convert_pdf import (
    PandocConversionError,
    convert_sopn_to_pdf,
)

from .models import OfficialDocument
from django.core.validators import FileExtensionValidator


class UploadDocumentForm(forms.ModelForm):
    class Meta:
        model = OfficialDocument
        fields = ("uploaded_file", "source_url", "ballot", "document_type")

        widgets = {"ballot": forms.HiddenInput()}

    uploaded_file = forms.FileField(
        validators=[
            FileExtensionValidator(allowed_extensions=["pdf", "docx", "html"])
        ]
    )

    document_type = forms.CharField(widget=forms.HiddenInput())

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
