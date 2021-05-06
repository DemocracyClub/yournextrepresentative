import faker
from django.test import TestCase

from elections.tests.test_ballot_view import SingleBallotStatesMixin
from uk_results.models import ResultSet

from ..models import Ballot

fake = faker.Faker()


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


class TestBallotQuerysetMethods(SingleBallotStatesMixin, TestCase):
    def setUp(self):
        self.election = self.create_election("local.sheffield.2021-05-06")
        self.post = self.create_post("Bar")
        self.parties = self.create_parties(3)

    def test_has_results_and_no_results(self):
        """
        Test that the has_results QS method only returns Ballots which either
        have a resultset, or have a candidate marked as elected. Test that
        no_results doesnt include Ballots that have a ResultSet or a candidate
        marked elected
        """
        no_results = []
        for i in range(5):
            ballot = self.create_ballot(
                ballot_paper_id=f"{fake.slug()}-{i}",
                post=self.post,
                election=self.election,
            )
            self.create_memberships(ballot=ballot, parties=self.parties)
            no_results.append(ballot)

        has_results = []
        for i in range(5):
            ballot = self.create_ballot(
                ballot_paper_id=f"{fake.slug()}-{i}",
                post=self.post,
                election=self.election,
            )
            self.create_memberships(ballot=ballot, parties=self.parties)
            ResultSet.objects.create(
                ballot=ballot,
                num_turnout_reported=10000,
                num_spoilt_ballots=30,
                source="Example ResultSet for testing",
            )
            has_results.append(ballot)

        has_winner_no_result = []
        for i in range(5):
            ballot = self.create_ballot(
                ballot_paper_id=f"{fake.slug()}-{i}",
                post=self.post,
                election=self.election,
            )
            self.create_memberships(ballot=ballot, parties=self.parties)
            winner = ballot.membership_set.first()
            winner.elected = True
            winner.save()
            has_winner_no_result.append(ballot)

        self.assertEqual(Ballot.objects.count(), 15)
        self.assertEqual(Ballot.objects.has_results().count(), 10)
        self.assertEqual(Ballot.objects.no_results().count(), 5)
        all_winners = set(has_results + has_winner_no_result)
        self.assertEqual(set(Ballot.objects.has_results()), all_winners)
        self.assertEqual(set(Ballot.objects.no_results()), set(no_results))
