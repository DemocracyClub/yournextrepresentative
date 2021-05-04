from django.test import TestCase

from ..models import Ballot


class TestBallotUrlMethods(TestCase):
    def setUp(self):
        self.ballot = Ballot(
            ballot_paper_id="local.sheffield.ecclesall.2021-05-06"
        )

    def test_get_absolute_url(self):
        url = self.ballot.get_absolute_url()
        assert url == f"/elections/{self.ballot.ballot_paper_id}/"

    def test_get_bulk_add_url(self):
        url = self.ballot.get_bulk_add_url()
        assert url == f"/bulk_adding/sopn/{self.ballot.ballot_paper_id}/"

    def test_get_bulk_add_review_url(self):
        url = self.ballot.get_bulk_add_review_url()
        assert url == f"/bulk_adding/sopn/{self.ballot.ballot_paper_id}/review/"

    def test_get_sopn_view(self):
        url = self.ballot.get_sopn_url()
        assert url == f"/elections/{self.ballot.ballot_paper_id}/sopn/"

    def test_get_results_url(self):
        fptp = Ballot(
            ballot_paper_id="local.sheffield.ecclesall.2021-05-06",
            voting_system=Ballot.VOTING_SYSTEM_FPTP,
        )
        other = Ballot(ballot_paper_id="gla.a.2021-05-06")
        assert (
            fptp.get_results_url()
            == "/uk_results/local.sheffield.ecclesall.2021-05-06/"
        )
        assert fptp.results_button_text == "Add results"
        assert other.get_results_url() == "/elections/gla.a.2021-05-06/"
        assert other.results_button_text == "Mark elected candidates"
