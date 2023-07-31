from django.urls import include, re_path
from elections.uk.views import frontpage, redirects

post_ignored_slug_re = r"(?!record-winner$|retract-winner$|.*\.csv$).*"

urlpatterns = [
    re_path(r"^bulk_adding/", include("bulk_adding.urls")),
    re_path(r"^uk_results/", include("uk_results.urls")),
    re_path(r"^$", frontpage.HomePageView.as_view(), name="lookup-postcode"),
    re_path(
        r"^postcode/(?P<postcode>[^/]+)/$",
        frontpage.PostcodeView.as_view(),
        name="postcode-view",
    ),
    re_path(
        r"^geolocator/(?P<latitude>[\d.\-]+),(?P<longitude>[\d.\-]+)",
        frontpage.GeoLocatorView.as_view(),
        name="geolocator",
    ),
    # These should all be redirects to the new URL scheme:
    re_path(
        r"^constituencies(?P<list_filter>|/unlocked|/declared)$",
        redirects.ConstituenciesRedirect.as_view(),
    ),
    re_path(
        r"^constituency/(?P<rest_of_path>.*)$",
        redirects.ConstituencyRedirect.as_view(),
    ),
    # This regex is to catch the /party and /parties URLs:
    re_path(r"^part(?P<rest_of_path>.*)$", redirects.PartyRedirect.as_view()),
    re_path(
        r"^candidacy(?P<rest_of_path>.*)$",
        redirects.CandidacyRedirect.as_view(),
    ),
    re_path(r"^person/create/$", redirects.PersonCreateRedirect.as_view()),
    re_path(
        r"^numbers/(?P<rest_of_path>constituencies|parties)$",
        redirects.CachedCountsRedirect.as_view(),
    ),
    re_path(
        r"^upload_document/upload/(?P<rest_of_path>[^/]*/)$",
        redirects.OfficialDocumentsRedirect.as_view(),
    ),
    re_path(r"^postcode_redirect/$", redirects.WhoPostcodeRedirect.as_view()),
    re_path(r"^get_involved/$", redirects.HelpOutCTAView.as_view()),
    re_path(
        r"^areas-of-type/(?P<area_type>.*?)(?:/(?P<ignored_slug>.*))?$",
        redirects.AreasOfTypeRedirectView.as_view(),
        name="areas-of-type-view",
    ),
]
