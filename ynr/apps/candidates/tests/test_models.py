import faker

from django.test import TestCase
from django.utils import timezone
from django.db.models import Q
from mock import patch

from candidates.tests.factories import (
    BallotPaperFactory,
    ElectionFactory,
    OrganizationFactory,
    PostFactory,
)
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


class BallotsWithResultsMixin(SingleBallotStatesMixin):
    """
    Test helper mixin to set up some ballots with results or candidates elected.
    TODO move this to a more sensible location, dont hardcode setup
    """

    def setUp(self):
        self.election = self.create_election(
            "local.sheffield.2021-05-06", date="2021-05-06"
        )
        self.post = self.create_post("Foo")
        self.parties = self.create_parties(3)

    def create_ballots_with_results(
        self, num, resultset=False, elected=False, num_winners=1, **kwargs
    ):
        results = []
        for i in range(num):
            ballot = self.create_ballot(
                post=self.post, election=self.election, **kwargs
            )
            self.create_memberships(ballot=ballot, parties=self.parties)

            if resultset:
                ResultSet.objects.create(
                    ballot=ballot,
                    num_turnout_reported=10000,
                    num_spoilt_ballots=30,
                    source="Example ResultSet for testing",
                )
                elected = True

            if elected:
                winners = ballot.membership_set.all()[:num_winners]
                for winner in winners:
                    winner.elected = True
                    winner.save()

            results.append(ballot)

        return results


class TestBallotQuerysetMethods(BallotsWithResultsMixin, TestCase):
    def test_has_results_and_no_results(self):
        """
        Test that the has_results QS method only returns Ballots which either
        have a resultset, or have a candidate marked as elected. Test that
        no_results doesnt include Ballots that have a ResultSet or a candidate
        marked elected
        """
        no_results = self.create_ballots_with_results(num=5, resultset=False)
        has_results = self.create_ballots_with_results(num=5, resultset=True)
        has_winner_no_result = self.create_ballots_with_results(
            num=5, resultset=False, elected=True
        )

        self.assertEqual(Ballot.objects.count(), 15)
        self.assertEqual(Ballot.objects.has_results().count(), 10)
        self.assertEqual(Ballot.objects.no_results().count(), 5)
        all_winners = set(has_results + has_winner_no_result)
        self.assertEqual(set(Ballot.objects.has_results()), all_winners)
        self.assertEqual(set(Ballot.objects.no_results()), set(no_results))

    @patch("candidates.models.popolo_extra.BallotQueryset.filter")
    def test_last_updated(self, mock_filter):
        """
        Unit test to ensure that when last_updated is called on the
        Ballot queryset the correct modified fields are filtered
        against.
        """
        datetime_obj = timezone.now()
        Ballot.objects.last_updated(datetime=datetime_obj)
        mock_filter.assert_called_once_with(
            Q(modified__gt=datetime_obj)
            | Q(election__modified__gt=datetime_obj)
            | Q(post__modified__gt=datetime_obj)
            | Q(membership__modified__gt=datetime_obj)
            | Q(membership__person__modified__gt=datetime_obj)
            | Q(membership__party__modified__gt=datetime_obj)
        )
        mock_filter.return_value.distinct.assert_called_once()

    def test_ordered_by_latest_ee_modified(self):
        """
        Create a batch of Ballots where the ee_modified date is a
        random date earlier than 'now'
        Then create a Ballot where the related Election has just been
        updated in EE.
        Call the method to order the ballots by latest_ee_modified and
        check that they were ordered with the one updated 'now' first
        """
        now = timezone.datetime.now()
        BallotPaperFactory.create_batch(
            size=100,
            ee_modified=fake.date_time_between(
                start_date="-30d", end_date=now, tzinfo=timezone.utc
            ),
            election=ElectionFactory(
                slug=fake.slug(),
                ee_modified=fake.date_time_between(
                    start_date="-30d", end_date=now, tzinfo=timezone.utc
                ),
            ),
            post=PostFactory(
                organization=OrganizationFactory(slug=fake.slug())
            ),
        )
        election_with_latest_ee_modified = ElectionFactory(
            slug=fake.slug(), ee_modified=now
        )
        expected = BallotPaperFactory(
            ee_modified=fake.date_time_between(
                start_date="-30d", end_date=now, tzinfo=timezone.utc
            ),
            election=election_with_latest_ee_modified,
            post=PostFactory(
                organization=OrganizationFactory(slug=fake.slug())
            ),
        )
        qs = Ballot.objects.ordered_by_latest_ee_modified()
        assert qs.first() == expected

        # now create a new Ballot where the ee_modified is 5 mins later
        # and the election ee_modified is older
        latest = now + timezone.timedelta(minutes=5)
        new_ballot = BallotPaperFactory(
            ee_modified=latest,
            election=ElectionFactory(
                ee_modified=fake.date_time_between(
                    start_date="-30d", end_date=now, tzinfo=timezone.utc
                )
            ),
            post=PostFactory(
                organization=OrganizationFactory(slug=fake.slug())
            ),
        )
        # get the queryset again
        qs = Ballot.objects.ordered_by_latest_ee_modified()
        # check that the new ballot is now the first returned
        assert qs.first() == new_ballot
