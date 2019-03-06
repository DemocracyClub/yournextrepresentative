from django.conf.urls import url

from .views import SingleWombleView, WombleTagsView, WombleTagView


urlpatterns = [
    url(r"^tags/$", WombleTagsView.as_view(), name="womble_tags"),
    url(r"^tags/(?P<tag>[^/]+)/$", WombleTagView.as_view(), name="womble_tag"),
    url(r"^(?P<pk>[\d]+)/$", SingleWombleView.as_view(), name="single_womble"),
]
