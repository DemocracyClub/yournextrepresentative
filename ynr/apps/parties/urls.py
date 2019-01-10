from django.conf.urls import url

from .views import CandidatesByElectionForPartyView


urlpatterns = [
    url(
        r"^(?P<party_id>[^/]+)/elections/(?P<election>[^/]+)/",
        CandidatesByElectionForPartyView.as_view(),
        name="candidates_by_election_for_party",
    )
]
