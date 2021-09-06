from django.urls import re_path

from . import views

urlpatterns = [
    re_path(
        r"^(?!.*party|sopn)(?P<ballot_paper_id>[^/]+)/$",
        views.BulkAddSOPNRedirectView.as_view(),
        name="bulk_add",
    ),
    re_path(
        r"^sopn/(?P<ballot_paper_id>[^/]+)/$",
        views.BulkAddSOPNView.as_view(),
        name="bulk_add_from_sopn",
    ),
    re_path(
        r"^sopn/(?P<ballot_paper_id>[^/]+)/review/$",
        views.BulkAddSOPNReviewView.as_view(),
        name="bulk_add_sopn_review",
    ),
    re_path(
        r"^party/(?P<election>[^/]+)/$",
        views.SelectPartyForm.as_view(),
        name="bulk_add_party_select",
    ),
    re_path(
        r"^party/(?P<election>[^/]+)/(?P<party_id>[^/]+)/$",
        views.BulkAddPartyView.as_view(),
        name="bulk_add_by_party",
    ),
    re_path(
        r"^party/(?P<election>[^/]+)/(?P<party_id>[^/]+)/review/$",
        views.BulkAddPartyReviewView.as_view(),
        name="bulk_add_by_party_review",
    ),
]
