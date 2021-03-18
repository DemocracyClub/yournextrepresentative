from django.conf.urls import url

from candidates import constants

from . import views

urlpatterns = [
    url(
        r"^(?!.*party|sopn)(?P<ballot_paper_id>[^/]+)/$",
        views.BulkAddSOPNRedirectView.as_view(),
        name="bulk_add",
    ),
    url(
        r"^sopn/(?P<ballot_paper_id>[^/]+)/$",
        views.BulkAddSOPNView.as_view(),
        name="bulk_add_from_sopn",
    ),
    url(
        r"^sopn/(?P<ballot_paper_id>[^/]+)/review/$",
        views.BulkAddSOPNReviewView.as_view(),
        name="bulk_add_sopn_review",
    ),
    url(
        r"^party/(?P<election>[^/]+)/$",
        views.SelectPartyForm.as_view(),
        name="bulk_add_party_select",
    ),
    url(
        r"^party/(?P<election>[^/]+)/(?P<party_id>[^/]+)/$",
        views.BulkAddPartyView.as_view(),
        name="bulk_add_by_party",
    ),
    url(
        r"^party/(?P<election>[^/]+)/(?P<party_id>[^/]+)/review/$",
        views.BulkAddPartyReviewView.as_view(),
        name="bulk_add_by_party_review",
    ),
]
