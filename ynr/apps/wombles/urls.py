from django.contrib.auth import views as auth_views
from django.urls import path, re_path

from .views import (
    AuthenticateView,
    LoginView,
    MyProfile,
    SingleWombleView,
    UpdateProfileDetailsView,
    WombleTagsView,
    WombleTagView,
)

app_name = "wombles"

urlpatterns = [
    path("me", MyProfile.as_view(), name="my_profile"),
    re_path(r"^tags/$", WombleTagsView.as_view(), name="womble_tags"),
    re_path(
        r"^tags/(?P<tag>[^/]+)/$", WombleTagView.as_view(), name="womble_tag"
    ),
    re_path(
        r"^(?P<pk>[\d]+)/$", SingleWombleView.as_view(), name="single_womble"
    ),
    path("login/", LoginView.as_view(), name="login"),
    path(
        "logout/",
        auth_views.LogoutView.as_view(template_name="wombles/logout.html"),
        name="logout",
    ),
    path("authenticate/", AuthenticateView.as_view(), name="authenticate"),
    path(
        "details",
        UpdateProfileDetailsView.as_view(),
        name="add_profile_details",
    ),
]
