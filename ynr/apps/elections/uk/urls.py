from django.conf import settings
from django.conf.urls import url, include

from elections.uk import views

post_ignored_slug_re = r"(?!record-winner$|retract-winner$|.*\.csv$).*"

urlpatterns = [
    url(r"^bulk_adding/", include("bulk_adding.urls")),
    url(r"^uk_results/", include("uk_results.urls")),
    url(r"^$", views.HomePageView.as_view(), name="lookup-postcode"),
    url(
        r"^postcode/(?P<postcode>[^/]+)/$",
        views.PostcodeView.as_view(),
        name="postcode-view",
    ),
    url(
        r"^geolocator/(?P<latitude>[\d.\-]+),(?P<longitude>[\d.\-]+)",
        views.GeoLocatorView.as_view(),
        name="geolocator",
    ),
    url(
        r"^election/{election}/post/(?P<post_id>[-\w\:]+)/(?P<ignored_slug>{ignore_pattern})$".format(
            election=r"(?P<election>[^/]+)", ignore_pattern=post_ignored_slug_re
        ),
        views.UKConstituencyDetailView.as_view(),
        name="constituency",
    ),
    url(
        r"^election/{election}/party/(?P<organization_id>[a-z-]+:[-\d]+)/(?P<ignored_slug>.*)$".format(
            election=r"(?P<election>[^/]+)"
        ),
        views.UKPartyDetailView.as_view(),
        name="party",
    ),
    # These should all be redirects to the new URL scheme:
    url(
        r"^constituencies(?P<list_filter>|/unlocked|/declared)$",
        views.ConstituenciesRedirect.as_view(),
    ),
    url(
        r"^constituency/(?P<rest_of_path>.*)$",
        views.ConstituencyRedirect.as_view(),
    ),
    # This regex is to catch the /party and /parties URLs:
    url(r"^part(?P<rest_of_path>.*)$", views.PartyRedirect.as_view()),
    url(r"^candidacy(?P<rest_of_path>.*)$", views.CandidacyRedirect.as_view()),
    url(r"^person/create/$", views.PersonCreateRedirect.as_view()),
    url(
        r"^numbers/(?P<rest_of_path>constituencies|parties)$",
        views.CachedCountsRedirect.as_view(),
    ),
    url(
        r"^upload_document/upload/(?P<rest_of_path>[^/]*/)$",
        views.OfficialDocumentsRedirect.as_view(),
    ),
    url(r"^postcode_redirect/$", views.WhoPostcodeRedirect.as_view()),
    url(r"^get_involved/$", views.HelpOutCTAView.as_view()),
    url(
        r"^areas-of-type/(?P<area_type>.*?)(?:/(?P<ignored_slug>.*))?$",
        views.AreasOfTypeRedirectView.as_view(),
        name="areas-of-type-view",
    ),
]
