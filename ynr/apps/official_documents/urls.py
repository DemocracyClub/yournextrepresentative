from django.urls import re_path
from django.views.decorators.csrf import csrf_exempt

from . import views

urlpatterns = [
    re_path(
        r"^posts_for_document/(?P<pk>\d+)/$",
        views.PostsForDocumentView.as_view(),
        name="posts_for_document",
    ),
    re_path(
        r"^uploaded/$",
        views.UnlockedWithDocumentsView.as_view(),
        name="unlocked_posts_with_documents",
    ),
    re_path(
        r"^election/(?P<election_id>[^/]+)/$",
        views.CreateElectionSOPNView.as_view(),
        name="upload_election_sopn_view",
    ),
    re_path(
        r"^election/(?P<election_id>[^/]+)/match_pages/$",
        csrf_exempt(views.ElectionSOPNMatchingView.as_view()),
        name="election_sopn_match_pages_view",
    ),
    re_path(
        r"^(?P<ballot_paper_id>[^/]+)/$",
        views.CreateBallotSOPNView.as_view(),
        name="upload_ballot_sopn_view",
    ),
]
