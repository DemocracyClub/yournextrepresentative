from django.urls import path

from .views import PersonSplitView

# Included at the site root, so the page sits with the other person pages
urlpatterns = [
    path(
        "person/<int:person_id>/split",
        PersonSplitView.as_view(),
        name="person-split",
    ),
]
