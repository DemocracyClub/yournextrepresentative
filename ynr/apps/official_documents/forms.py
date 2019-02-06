from django import forms

from .models import OfficialDocument


class UploadDocumentForm(forms.ModelForm):
    class Meta:
        model = OfficialDocument
        fields = (
            "uploaded_file",
            "source_url",
            "post_election",
            "document_type",
        )

        widgets = {
            "post": forms.HiddenInput(),
            "election": forms.HiddenInput(),
            "post_election": forms.HiddenInput(),
        }

    document_type = forms.CharField(widget=forms.HiddenInput())
