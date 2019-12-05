from django.conf.urls import include, url
from django.views.decorators.cache import cache_page
from django.views.generic import TemplateView, RedirectView
from rest_framework import routers

import elections.api.next.api_views
import parties.api.next.api_views
import people.api.next.api_views
from api import slack_hooks
from api.next import views as next_views
from api.v09 import views as v09views
from api.views import (
    APIDocsEndpointsView,
    APIDocsDefinitionsView,
    NextAPIDocsView,
    CSVListView,
)
from parties.api.next.api_views import PartyViewSet, PartyRegisterList
from uk_results.api.v09.api_views import (
    CandidateResultViewSet,
    ResultSetViewSet,
)
from uk_results.api.next.api_views import ResultViewSet, ElectedViewSet

v09_api_router = routers.DefaultRouter()

v09_api_router.register(r"persons", v09views.PersonViewSet, basename="person")
v09_api_router.register(r"organizations", v09views.OrganizationViewSet)
v09_api_router.register(r"posts", v09views.PostViewSet)
v09_api_router.register(r"elections", v09views.ElectionViewSet)
v09_api_router.register(r"party_sets", v09views.PartySetViewSet)
v09_api_router.register(r"post_elections", v09views.PostExtraElectionViewSet)
v09_api_router.register(r"memberships", v09views.MembershipViewSet)
v09_api_router.register(r"logged_actions", v09views.LoggedActionViewSet)
v09_api_router.register(
    r"extra_fields", v09views.ExtraFieldViewSet, basename="extra_fields"
)
v09_api_router.register(r"person_redirects", v09views.PersonRedirectViewSet)

v09_api_router.register(r"candidate_results", CandidateResultViewSet)
v09_api_router.register(r"result_sets", ResultSetViewSet)

v09_api_router.register(
    r"candidates_for_postcode",
    v09views.CandidatesAndElectionsForPostcodeViewSet,
    basename="candidates-for-postcode",
)

# "Next" is the label we give to the "bleeding edge" or unstable API
next_api_router = routers.DefaultRouter()
next_api_router.register(
    r"people", people.api.next.api_views.PersonViewSet, basename="person"
)
next_api_router.register(r"organizations", next_views.OrganizationViewSet)
next_api_router.register(
    r"elections", elections.api.next.api_views.ElectionViewSet
)
next_api_router.register(
    r"election_types",
    elections.api.next.api_views.ElectionTypesList,
    basename="election_types",
)
next_api_router.register(r"ballots", elections.api.next.api_views.BallotViewSet)
next_api_router.register(r"logged_actions", next_views.LoggedActionViewSet)
next_api_router.register(
    r"person_redirects", people.api.next.api_views.PersonRedirectViewSet
)

next_api_router.register(r"parties", PartyViewSet)
next_api_router.register(
    r"party_registers", PartyRegisterList, basename="party_register"
)
next_api_router.register(r"results", ResultViewSet)
next_api_router.register(r"candidates_elected", ElectedViewSet)


urlpatterns = [
    # Router views
    url(r"^api/(?P<version>v0.9)/", include(v09_api_router.urls)),
    url(r"^api/(?P<version>next)/", include(next_api_router.urls)),
    url(
        r"^api/docs/$",
        TemplateView.as_view(template_name="api/api-home.html"),
        name="api-home",
    ),
    url(
        r"^api/$",
        RedirectView.as_view(url="/api/docs/"),
        name="api-docs-redirect",
    ),
    url(
        r"^api/docs/terms/$",
        TemplateView.as_view(template_name="api/terms.html"),
        name="api-terms",
    ),
    url(r"^api/docs/csv/$", CSVListView.as_view(), name="api_docs_csv"),
    url(
        r"^api/docs/next/$",
        NextAPIDocsView.as_view(patterns=next_api_router.urls, version="next"),
        name="api_docs_next_home",
    ),
    url(
        r"^api/docs/next/endpoints/$",
        APIDocsEndpointsView.as_view(
            patterns=next_api_router.urls, version="next"
        ),
        name="api_docs_next_endpoints",
    ),
    url(
        r"^api/docs/next/definitions/$",
        APIDocsDefinitionsView.as_view(
            patterns=next_api_router.urls, version="next"
        ),
        name="api_docs_next_definitions",
    ),
    # Standard Django views
    url(
        r"^api/current-elections",
        v09views.CurrentElectionsView.as_view(),
        name="current-elections",
    ),
    url(
        r"^post-id-to-party-set.json$",
        cache_page(60 * 60)(v09views.PostIDToPartySetView.as_view()),
        name="post-id-to-party-set",
    ),
    url(
        r"^all-parties.json$",
        cache_page(60 * 60)(
            parties.api.next.api_views.AllPartiesJSONView.as_view()
        ),
        name="all-parties-json-view",
    ),
    url(r"^version.json", v09views.VersionView.as_view(), name="version"),
    url(
        r"^upcoming-elections",
        v09views.UpcomingElectionsView.as_view(),
        name="upcoming-elections",
    ),
    url("api/slack-hooks", slack_hooks.SlackHookRouter.as_view()),
]
