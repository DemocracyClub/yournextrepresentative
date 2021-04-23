from django.urls import path

from .views import DuplicateSuggestionListView, RejectSuggestion

urlpatterns = [
    path(
        "<int:pk>/reject", RejectSuggestion.as_view(), name="duplicate-reject"
    ),
    path("", DuplicateSuggestionListView.as_view(), name="duplicate-list"),
]
