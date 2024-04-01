from django.urls import re_path
from elections import views
from elections.helpers import ElectionIDSwitcher

urlpatterns = [
    re_path(
        "^elections/$",
        views.ElectionListView.as_view(),
        name="election_list_view",
    ),
    re_path(
        "^elections/(?P<election>[^/]+)/$",
        ElectionIDSwitcher(
            election_view=views.ElectionView, ballot_view=views.BallotPaperView
        ),
        name="election_view",
    ),
    re_path(
        r"^elections/(?P<election>[^/]+)/unlocked/",
        views.UnlockedBallotsForElectionListView.as_view(),
        name="constituencies-unlocked",
    ),
    re_path(
        r"^election/(?P<ballot_id>[^/]+)/lock/",
        views.LockBallotView.as_view(),
        name="constituency-lock",
    ),
    re_path(
        r"^elections/(?P<ballot_id>[^/]+)/sopn/",
        views.SOPNForBallotView.as_view(),
        name="ballot_paper_sopn",
    ),
    re_path(
        r"^elections/(?P<election_id>[^/]+)/election-sopn/",
        views.SOPNForElectionView.as_view(),
        name="election_sopn",
    ),
    re_path(
        r"^elections/(?P<ballot_id>[^/]+)/(?P<party_id>[^/]+)/",
        views.PartyForBallotView.as_view(),
        name="party-for-ballot",
    ),
    re_path(
        r"^elections/(?P<ballot_id>[^/]+).csv",
        views.BallotPaperCSVView.as_view(),
        name="ballot_paper_csv",
    ),
    re_path(
        r"^ajax/ballots/ballots_for_select.json",
        views.BallotsForSelectAjaxView.as_view(),
        name="ajax_ballots_for_select",
    ),
]
