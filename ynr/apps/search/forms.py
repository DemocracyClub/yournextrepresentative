from django.forms import forms
from django.utils.html import escape

from search.utils import search_person_by_name


class PersonSearchForm(forms.Form):
    def clean_q(self):
        return escape(self.cleaned_data["q"])

    def search(self):
        return search_person_by_name(self.cleaned_data["q"])[:10]
