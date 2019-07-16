from django import forms

from .models import OfficialDocument


class UploadDocumentForm(forms.ModelForm):
    class Meta:
        model = OfficialDocument
        fields = ("uploaded_file", "source_url", "ballot", "document_type")

        widgets = {"ballot": forms.HiddenInput()}

    document_type = forms.CharField(widget=forms.HiddenInput())
