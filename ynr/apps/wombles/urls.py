from django.urls import re_path

from .views import SingleWombleView, WombleTagsView, WombleTagView

urlpatterns = [
    re_path(r"^tags/$", WombleTagsView.as_view(), name="womble_tags"),
    re_path(
        r"^tags/(?P<tag>[^/]+)/$", WombleTagView.as_view(), name="womble_tag"
    ),
    re_path(
        r"^(?P<pk>[\d]+)/$", SingleWombleView.as_view(), name="single_womble"
    ),
]
