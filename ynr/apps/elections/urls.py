from django.conf.urls import url

from elections import views
from elections.helpers import ElectionIDSwitcher

urlpatterns = [
    url(
        "elections/$",
        views.ElectionListView.as_view(),
        name="election_list_view",
    ),
    url(
        "elections/(?P<election>[^/]+)/$",
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
]
