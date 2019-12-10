from django.conf.urls import url

from .views import PersonFacebookAdsView

urlpatterns = [
    url(
        r"^person/(?P<person_id>[\d]+)/facebook_ads/",
        PersonFacebookAdsView.as_view(),
        name="person_facebook_ads",
    )
]
