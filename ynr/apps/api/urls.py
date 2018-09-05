from django.conf.urls import include, url

from rest_framework import routers

from candidates import views
from parties.api_views import PartyViewSet
from uk_results.views import CandidateResultViewSet, ResultSetViewSet

v09_api_router = routers.DefaultRouter()

v09_api_router.register(r"persons", views.PersonViewSet, base_name="person")
v09_api_router.register(r"organizations", views.v09OrganizationViewSet)
v09_api_router.register(r"posts", views.PostViewSet)
v09_api_router.register(r"elections", views.ElectionViewSet)
v09_api_router.register(r"party_sets", views.PartySetViewSet)
v09_api_router.register(r"images", views.ImageViewSet)
v09_api_router.register(r"post_elections", views.PostExtraElectionViewSet)
v09_api_router.register(r"memberships", views.MembershipViewSet)
v09_api_router.register(r"logged_actions", views.LoggedActionViewSet)
v09_api_router.register(r"extra_fields", views.ExtraFieldViewSet)
v09_api_router.register(r"complex_fields", views.ComplexPopoloFieldViewSet)
v09_api_router.register(r"person_redirects", views.PersonRedirectViewSet)

v09_api_router.register(r"candidate_results", CandidateResultViewSet)
v09_api_router.register(r"result_sets", ResultSetViewSet)

v09_api_router.register(
    r"candidates_for_postcode",
    views.CandidatesAndElectionsForPostcodeViewSet,
    base_name="candidates-for-postcode",
)

# "Next" is the label we give to the "bleeding edge" or unstable API
next_api_router = routers.DefaultRouter()
next_api_router.register(r"persons", views.PersonViewSet, base_name="person")
next_api_router.register(r"organizations", views.OrganizationViewSet)
next_api_router.register(r"posts", views.PostViewSet)
next_api_router.register(r"elections", views.ElectionViewSet)
next_api_router.register(r"party_sets", views.PartySetViewSet)
next_api_router.register(r"images", views.ImageViewSet)
next_api_router.register(r"post_elections", views.PostExtraElectionViewSet)
next_api_router.register(r"memberships", views.MembershipViewSet)
next_api_router.register(r"logged_actions", views.LoggedActionViewSet)
next_api_router.register(r"extra_fields", views.ExtraFieldViewSet)
next_api_router.register(r"complex_fields", views.ComplexPopoloFieldViewSet)
next_api_router.register(r"person_redirects", views.PersonRedirectViewSet)

next_api_router.register(r"candidate_results", CandidateResultViewSet)
next_api_router.register(r"result_sets", ResultSetViewSet)
next_api_router.register(r"parties", PartyViewSet)

next_api_router.register(
    r"candidates_for_postcode",
    views.CandidatesAndElectionsForPostcodeViewSet,
    base_name="candidates-for-postcode",
)


urlpatterns = [
    url(r"^api/(?P<version>v0.9)/", include(v09_api_router.urls)),
    url(r"^api/(?P<version>next)/", include(next_api_router.urls)),
]
