from django.conf.urls import include, url

from elections.uk.views import frontpage, redirects

post_ignored_slug_re = r"(?!record-winner$|retract-winner$|.*\.csv$).*"

urlpatterns = [
    url(r"^bulk_adding/", include("bulk_adding.urls")),
    url(r"^uk_results/", include("uk_results.urls")),
    url(r"^$", frontpage.HomePageView.as_view(), name="lookup-postcode"),
    url(
        r"^postcode/(?P<postcode>[^/]+)/$",
        frontpage.PostcodeView.as_view(),
        name="postcode-view",
    ),
    url(
        r"^geolocator/(?P<latitude>[\d.\-]+),(?P<longitude>[\d.\-]+)",
        frontpage.GeoLocatorView.as_view(),
        name="geolocator",
    ),
    # These should all be redirects to the new URL scheme:
    url(
        r"^constituencies(?P<list_filter>|/unlocked|/declared)$",
        redirects.ConstituenciesRedirect.as_view(),
    ),
    url(
        r"^constituency/(?P<rest_of_path>.*)$",
        redirects.ConstituencyRedirect.as_view(),
    ),
    # This regex is to catch the /party and /parties URLs:
    url(r"^part(?P<rest_of_path>.*)$", redirects.PartyRedirect.as_view()),
    url(
        r"^candidacy(?P<rest_of_path>.*)$",
        redirects.CandidacyRedirect.as_view(),
    ),
    url(r"^person/create/$", redirects.PersonCreateRedirect.as_view()),
    url(
        r"^numbers/(?P<rest_of_path>constituencies|parties)$",
        redirects.CachedCountsRedirect.as_view(),
    ),
    url(
        r"^upload_document/upload/(?P<rest_of_path>[^/]*/)$",
        redirects.OfficialDocumentsRedirect.as_view(),
    ),
    url(r"^postcode_redirect/$", redirects.WhoPostcodeRedirect.as_view()),
    url(r"^get_involved/$", redirects.HelpOutCTAView.as_view()),
    url(
        r"^areas-of-type/(?P<area_type>.*?)(?:/(?P<ignored_slug>.*))?$",
        redirects.AreasOfTypeRedirectView.as_view(),
        name="areas-of-type-view",
    ),
]
