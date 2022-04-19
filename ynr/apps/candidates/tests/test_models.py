import faker
from django.test import TestCase, RequestFactory
from django.contrib.auth.models import User

from django.utils import timezone
from django.db.models import Max
from django.db.models.functions import Greatest
from mock import patch
from candidates.models.db import ActionType

from candidates.tests.factories import (
    BallotPaperFactory,
    ElectionFactory,
    OrganizationFactory,
    PostFactory,
)
from elections.tests.test_ballot_view import SingleBallotStatesMixin
from moderation_queue.tests.factories import QueuedImageFactory
from uk_results.models import ResultSet

from candidates.models import Ballot
from candidates.tests.factories import MembershipFactory
from people.tests.factories import PersonFactory
from candidates.models import LoggedAction

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


class TestBallotMethods(TestCase, SingleBallotStatesMixin):
    def setUp(self):
        self.factory = RequestFactory()
        self.user = User.objects.create_user(
            username="jacob", email="jacob@…", password="top_secret"
        )

        election = self.create_election("Sheffield Local Election")
        post = self.create_post(post_label="Ecclesall")
        self.ballot = self.create_ballot(
            ballot_paper_id="local.sheffield.ecclesall.2021-05-06",
            election=election,
            post=post,
            winner_count=2,
            candidates_locked=True,
        )

    def create_memberships(self, parties, candidates_per_party=1):
        for i in range(candidates_per_party):
            for party in parties:
                person = PersonFactory()
                MembershipFactory(
                    ballot=self.ballot, person=person, party=party
                )

    def test_uncontested_when_winner_count_same_as_memberships(self):
        parties = self.create_parties(2)
        self.create_memberships(parties)
        self.assertTrue(self.ballot.uncontested)

    def test_uncontested_when_winner_count_is_less_than_memberships(self):
        parties = self.create_parties(3)
        self.create_memberships(parties)
        self.assertFalse(self.ballot.uncontested)

    def test_uncontested_when_winner_count_is_more_than_memberships(self):
        parties = self.create_parties(1)
        self.create_memberships(parties)
        self.assertTrue(self.ballot.uncontested)

    def test_mark_uncontested_winners(self):
        parties = self.create_parties(2)

        self.create_memberships(parties)
        self.assertTrue(self.ballot.uncontested)
        self.ballot.mark_uncontested_winners(
            ip_address="111.11.1111", user=self.user
        )
        self.assertTrue(
            self.ballot.membership_set.filter(elected=True).count(), 2
        )
        self.assertEqual(LoggedAction.objects.count(), 2)

    def test_unmark_uncontested_winners_without_results(self):
        """
        Test that if there were no candidates marked as elected, do nothing
        """
        parties = self.create_parties(3)
        self.create_memberships(parties)
        self.assertFalse(self.ballot.has_results)
        self.ballot.unmark_uncontested_winners(
            ip_address="111.11.1111", user=self.user
        )
        self.assertEqual(
            self.ballot.membership_set.filter(elected=True).count(), 0
        )
        self.assertEqual(LoggedAction.objects.count(), 0)
        self.assertEqual(
            self.ballot.membership_set.filter(elected=None).count(), 3
        )

    def test_unmark_uncontested_winners_with_results(self):
        """
        Test that if there were candidates were marked as elected as
        the marked uncontested, that the winners are unset and logged actions created
        """
        parties = self.create_parties(2)
        self.create_memberships(parties)
        self.assertTrue(self.ballot.uncontested)
        self.ballot.mark_uncontested_winners()
        self.assertEqual(
            self.ballot.membership_set.filter(elected=True).count(), 2
        )
        self.ballot.unmark_uncontested_winners(
            ip_address="111.11.1111", user=self.user
        )
        self.assertEqual(
            self.ballot.membership_set.filter(elected=True).count(), 0
        )
        self.assertEqual(
            LoggedAction.objects.filter(
                action_type=ActionType.SET_CANDIDATE_NOT_ELECTED
            ).count(),
            2,
        )
        self.assertEqual(
            self.ballot.membership_set.filter(elected=None).count(), 2
        )

    def test_unmark_uncontested_winners_unmarks_winners_if_was_uncontested(
        self,
    ):
        """
        Test that if there were candidates were marked as elected as
        the marked uncontested, that the winners are unset and logged actions created
        """
        parties = self.create_parties(2)
        self.create_memberships(parties)
        self.assertTrue(self.ballot.uncontested)
        self.ballot.mark_uncontested_winners()
        self.assertEqual(
            self.ballot.membership_set.filter(elected=True).count(), 2
        )
        # unlock the ballot
        self.ballot.locked = False
        self.ballot.save()
        self.ballot.unmark_uncontested_winners(
            ip_address="111.11.1111", user=self.user
        )
        self.assertEqual(
            self.ballot.membership_set.filter(elected=True).count(), 0
        )
        self.assertEqual(
            LoggedAction.objects.filter(
                action_type=ActionType.SET_CANDIDATE_NOT_ELECTED
            ).count(),
            2,
        )
        self.assertEqual(
            self.ballot.membership_set.filter(elected=None).count(), 2
        )

    def test_get_absolute_queued_image_review_url(self):
        parties = self.create_parties(3)
        self.create_memberships(parties)
        self.assertEqual(self.ballot.get_absolute_queued_image_review_url, "")
        person = self.ballot.membership_set.first().person
        # create a queued image for a candidate in the ballot
        QueuedImageFactory(person=person)
        # lookup the ballot again to clear cache
        ballot = Ballot.objects.get(pk=self.ballot.pk)
        self.assertEqual(
            ballot.get_absolute_queued_image_review_url,
            f"/moderation/photo/review?ballot_paper_id={self.ballot.ballot_paper_id}",
        )

    def test_is_welsh_run_false(self):
        non_welsh_election_types = [
            "parl.",
            "nia.",
            "europarl.",
            "sp.",
            "gla.",
            "ref.",
            # TODO confirm if these could be welsh run?
            "pcc." "mayor.",
            # TODO check this one
            "naw.",
        ]
        for election_type in non_welsh_election_types:
            ballot = Ballot(ballot_paper_id=election_type)
            with self.subTest(msg=election_type):
                self.assertFalse(ballot.is_welsh_run)

        non_welsh_nuts1_codes = [
            "UKC",
            "UKD",
            "UKE",
            "UKF",
            "UKG",
            "UKH",
            "UKI",
            "UKJ",
            "UKK",
            "UKM",
            "UKN",
        ]
        for nuts_code in non_welsh_nuts1_codes:
            non_welsh_local_ballot = Ballot(
                ballot_paper_id="local.",
                tags={"NUTS1": {"key": nuts_code, "value": ""}},
            )
            with self.subTest(msg=nuts_code):
                self.assertFalse(non_welsh_local_ballot.is_welsh_run)

    def test_is_welsh_run_true(self):
        welsh_ballots = [
            Ballot(ballot_paper_id="senedd."),
            Ballot(
                ballot_paper_id="local.",
                tags={"NUTS1": {"key": "UKL", "value": ""}},
            ),
        ]
        for ballot in welsh_ballots:
            with self.subTest(msg=str(ballot)):
                self.assertTrue(ballot.is_welsh_run)


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


class TestHasResultsOrNoResults(BallotsWithResultsMixin, TestCase):
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

    @patch("candidates.models.popolo_extra.BallotQueryset.with_last_updated")
    def test_last_updated(self, mock_with_last_updated):
        """
        Unit test to ensure that when last_updated is called on the
        Ballot queryset the correct modified fields are filtered
        against.
        """
        datetime_obj = timezone.now()
        Ballot.objects.last_updated(datetime=datetime_obj)
        mock_with_last_updated.assert_called_once()
        mock_with_last_updated.return_value.filter.assert_called_once_with(
            last_updated__gte=datetime_obj
        )

    @patch("candidates.models.popolo_extra.BallotQueryset.annotate")
    def test_with_last_updated(self, mock_annotate):
        Ballot.objects.with_last_updated()
        mock_annotate.assert_called_once_with(
            membership_modified_max=Max("membership__modified"),
            last_updated=Greatest(
                "modified",
                "election__modified",
                "post__modified",
                "membership_modified_max",
            ),
        )
        mock_annotate.return_value.distinct.assert_called_once()
        mock_annotate.return_value.distinct.return_value.order_by.assert_called_once_with(
            "last_updated"
        )

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


class TestBallotQuerySetMethods(TestCase, SingleBallotStatesMixin):
    def create_memberships(self, ballot, parties, candidates_per_party=1):
        for i in range(candidates_per_party):
            for party in parties:
                person = PersonFactory()
                MembershipFactory(ballot=ballot, person=person, party=party)

    def test_uncontested_no_candidates(self):
        election = self.create_election("Strensall Local Election")
        post = self.create_post(post_label="Strensall")
        ballot = self.create_ballot(
            ballot_paper_id="local.york.strensall.2019-05-02",
            election=election,
            post=post,
            winner_count=1,
            candidates_locked=True,
        )
        uncontested_ballots = Ballot.objects.uncontested()
        self.assertIn(ballot, uncontested_ballots)

    def test_uncontested_unlocked(self):
        election = self.create_election("Strensall Local Election")
        post = self.create_post(post_label="Strensall")
        ballot = self.create_ballot(
            ballot_paper_id="local.york.strensall.2020-05-06",
            election=election,
            post=post,
            winner_count=1,
            candidates_locked=False,
        )
        parties = self.create_parties(1)
        self.create_memberships(ballot, parties)
        uncontested_ballots = Ballot.objects.uncontested()
        self.assertNotIn(ballot, uncontested_ballots)

    def test_uncontested_more_than_winner_count(self):
        election = self.create_election("Strensall Local Election")
        post = self.create_post(post_label="St Mary's")
        ballot = self.create_ballot(
            ballot_paper_id="local.adur.st-marys.2021-05-06",
            election=election,
            post=post,
            winner_count=1,
            candidates_locked=True,
        )
        parties = self.create_parties(2)
        self.create_memberships(ballot, parties)
        uncontested_ballots = Ballot.objects.uncontested()
        self.assertNotIn(ballot, uncontested_ballots)

    def test_uncontested_less_than_winner_count(self):
        election = self.create_election("Strensall Local Election")
        post = self.create_post(post_label="St Mary's")
        ballot = self.create_ballot(
            ballot_paper_id="local.adur.st-marys.2021-05-06",
            election=election,
            post=post,
            winner_count=2,
            candidates_locked=True,
        )
        parties = self.create_parties(1)
        self.create_memberships(ballot, parties)
        uncontested_ballots = Ballot.objects.uncontested()
        self.assertIn(ballot, uncontested_ballots)

    def test_uncontested_match_winner_count(self):
        election = self.create_election("Strensall Local Election")
        election.slug = "local.adur.2021-05-06"
        post = self.create_post(post_label="Strensall")
        ballot = self.create_ballot(
            ballot_paper_id="local.strensall.foo.2020-05-06",
            election=election,
            post=post,
            winner_count=2,
            candidates_locked=True,
        )
        parties = self.create_parties(2)
        self.create_memberships(ballot, parties)
        uncontested_ballots = Ballot.objects.uncontested()
        self.assertIn(ballot, uncontested_ballots)

    def test_looks_uncontested(self):
        election = self.create_election("Strensall Local Election")
        election.slug = "local.adur.2021-05-06"
        post = self.create_post(post_label="Strensall")
        ballot = self.create_ballot(
            ballot_paper_id="local.strensall.foo.2020-05-06",
            election=election,
            post=post,
            winner_count=2,
            candidates_locked=False,
        )
        for case in [
            {"num_parties": 1, "expected": True},
            {"num_parties": 2, "expected": True},
            {"num_parties": 3, "expected": False},
        ]:
            with self.subTest(msg=case["num_parties"]):
                parties = self.create_parties(case["num_parties"])
                self.create_memberships(ballot, parties)
                self.assertEqual(ballot.looks_uncontested, case["expected"])
                ballot.membership_set.all().delete()
