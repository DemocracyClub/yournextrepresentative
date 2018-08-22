from django.conf.urls import url

from .views import CandidatesByElectionForPartyView


urlpatterns = [
    url(
        r"^(?P<election>[^/]+)/(?P<party_id>[^/]+)/",
        CandidatesByElectionForPartyView.as_view(),
        name="candadidtes_by_election_for_party",
    )
]
