from django.urls import re_path

from .views import PersonFacebookAdsView

urlpatterns = [
    re_path(
        r"^person/(?P<person_id>[\d]+)/facebook_ads/",
        PersonFacebookAdsView.as_view(),
        name="person_facebook_ads",
    )
]
