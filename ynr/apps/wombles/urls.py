from django.urls import path, re_path

from .views import MyProfile, SingleWombleView, WombleTagsView, WombleTagView

urlpatterns = [
    path("me", MyProfile.as_view(), name="my_profile"),
    re_path(r"^tags/$", WombleTagsView.as_view(), name="womble_tags"),
    re_path(
        r"^tags/(?P<tag>[^/]+)/$", WombleTagView.as_view(), name="womble_tag"
    ),
    re_path(
        r"^(?P<pk>[\d]+)/$", SingleWombleView.as_view(), name="single_womble"
    ),
]
