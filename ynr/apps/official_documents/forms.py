from django import forms

from .models import OfficialDocument
from django.core.validators import FileExtensionValidator


class UploadDocumentForm(forms.ModelForm):
    class Meta:
        model = OfficialDocument
        fields = ("uploaded_file", "source_url", "ballot", "document_type")

        widgets = {"ballot": forms.HiddenInput()}

    uploaded_file = forms.FileField(
        validators=[FileExtensionValidator(allowed_extensions=["pdf"])]
    )

    document_type = forms.CharField(widget=forms.HiddenInput())
