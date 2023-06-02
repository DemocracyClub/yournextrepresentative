from django.urls import re_path

from .views import CandidatesByElectionForPartyView, PartyView

urlpatterns = [
    re_path(r"^(?P<ec_id>[^/]+)", PartyView.as_view()),
    re_path(
        r"^(?P<party_id>[^/]+)/elections/(?P<election>[^/]+)/",
        CandidatesByElectionForPartyView.as_view(),
        name="candidates_by_election_for_party",
    ),
]
