from django.contrib import messages
from django.views.generic import ListView, UpdateView
from django.urls import reverse_lazy

from auth_helpers.views import GroupRequiredMixin
from candidates.models.auth import TRUSTED_TO_MERGE_GROUP_NAME

from .models import DuplicateSuggestion
from .forms import RejectionForm


class DuplicateSuggestionListView(GroupRequiredMixin, ListView):
    model = DuplicateSuggestion
    required_group_name = TRUSTED_TO_MERGE_GROUP_NAME

    def get_queryset(self):
        """
        Only display suggestions that are open
        """
        return DuplicateSuggestion.objects.open()


class RejectSuggestion(GroupRequiredMixin, UpdateView):
    http_method_names = ["post"]
    form_class = RejectionForm
    required_group_name = TRUSTED_TO_MERGE_GROUP_NAME
    model = DuplicateSuggestion
    success_url = reverse_lazy("duplicate-list")
    success_message = "Duplicate rejected"

    def get_queryset(self):
        """
        Ensures only open suggestions can be rejected
        """
        return DuplicateSuggestion.objects.open()

    def form_valid(self, form):
        """
        Adds success message
        """
        response = super().form_valid(form)
        msg = f"Duplicate between {self.object.person.name} and {self.object.other_person.name} was rejected"
        messages.add_message(
            request=self.request,
            level=messages.SUCCESS,
            message=msg,
            extra_tags="safe do-something-else",
        )
        return response
