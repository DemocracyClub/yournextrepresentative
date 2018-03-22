from django.views.generic import ListView

from .models import DuplicateSuggestion


class DuplicateSuggestionListView(ListView):
    model = DuplicateSuggestion
