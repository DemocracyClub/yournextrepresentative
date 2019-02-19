from django.conf.urls import url

from elections import views
from elections.helpers import ElectionIDSwitcher

urlpatterns = [
    url(
        "^elections/$",
        views.ElectionListView.as_view(),
        name="election_list_view",
    ),
    url(
        "^elections/(?P<election>[^/]+)/$",
        ElectionIDSwitcher(
            election_view=views.ElectionView, ballot_view=views.BallotPaperView
        ),
        name="election_view",
    ),
    url(
        r"^elections/(?P<election>[^/]+)/unlocked/",
        views.UnlockedBallotsForElectionListView.as_view(),
        name="constituencies-unlocked",
    ),
    url(
        r"^election/(?P<ballot_id>[^/]+)/lock/",
        views.LockBallotView.as_view(),
        name="constituency-lock",
    ),
    url(
        r"^elections/(?P<ballot_id>[^/]+)/sopn/",
        views.SOPNForBallotView.as_view(),
        name="ballot_paper_sopn",
    ),
    url(
        r"^elections/(?P<ballot_id>[^/]+).csv",
        views.BallotPaperCSVView.as_view(),
        name="ballot_paper_csv",
    ),
]
