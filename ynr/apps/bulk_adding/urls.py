from django.conf.urls import url

from candidates import constants

from . import views

urlpatterns = [
    url(
        r"^(?!.*party|sopn){election}/{post}/$".format(
            election=constants.ELECTION_ID_REGEX, post=constants.POST_ID_REGEX
        ),
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
        r"^party/{election}/$".format(election=constants.ELECTION_ID_REGEX),
        views.SelectPartyForm.as_view(),
        name="bulk_add_party_select",
    ),
    url(
        r"^party/{election}/(?P<party_id>[^/]+)/$".format(
            election=constants.ELECTION_ID_REGEX
        ),
        views.BulkAddPartyView.as_view(),
        name="bulk_add_by_party",
    ),
    url(
        r"^party/{election}/(?P<party_id>[^/]+)/review/$".format(
            election=constants.ELECTION_ID_REGEX
        ),
        views.BulkAddPartyReviewView.as_view(),
        name="bulk_add_by_party_review",
    ),
]
