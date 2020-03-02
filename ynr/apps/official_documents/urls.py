from django.conf.urls import url

from . import views

urlpatterns = [
    url(
        r"^(?P<ballot_paper_id>[^/]+)/$",
        views.CreateDocumentView.as_view(),
        name="upload_document_view",
    ),
    url(
        r"^posts_for_document/(?P<pk>\d+)/$",
        views.PostsForDocumentView.as_view(),
        name="posts_for_document",
    ),
    url(
        r"^uploaded/$",
        views.UnlockedWithDocumentsView.as_view(),
        name="unlocked_posts_with_documents",
    ),
]
