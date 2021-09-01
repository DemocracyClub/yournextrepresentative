from django.urls import re_path

from .views import CandidatesByElectionForPartyView

urlpatterns = [
    re_path(
        r"^(?P<party_id>[^/]+)/elections/(?P<election>[^/]+)/",
        CandidatesByElectionForPartyView.as_view(),
        name="candidates_by_election_for_party",
    )
]
