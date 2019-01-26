from django.conf.urls import url

from .views import SingleWombleView


urlpatterns = [
    url(r"^(?P<pk>[^/]+)/$", SingleWombleView.as_view(), name="single_womble")
]
