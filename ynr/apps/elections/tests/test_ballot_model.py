import datetime

import mock
from candidates.models import Ballot
from candidates.tests.uk_examples import UK2015ExamplesMixin
from django.test import TestCase
from django.utils import timezone


class ElectionTests(UK2015ExamplesMixin, TestCase):
    def test_get_previous_ballot_for_post(self):
        self.assertEqual(
            Ballot.objects.get_previous_ballot_for_post(
                self.edinburgh_east_post_ballot
            ),
            self.edinburgh_east_post_ballot_earlier,
        )

    def test_get_previous_ballot_for_post_no_previous(self):
        self.assertIsNone(
            Ballot.objects.get_previous_ballot_for_post(
                self.edinburgh_east_post_ballot_earlier
            )
        )

    def test_polls_closed_election_in_long_past(self):
        self.assertTrue(self.edinburgh_east_post_ballot_earlier.polls_closed)

    def test_polls_closed_election_in_future(self):
        self.edinburgh_east_post_ballot.election.refresh_from_db()
        self.assertFalse(self.edinburgh_east_post_ballot.polls_closed)

    @mock.patch("django.utils.timezone.now")
    def test_polls_closed_election_later_today(self, mock_now):
        mock_now.return_value = timezone.make_aware(
            datetime.datetime(2019, 1, 1, 10, 10, 10)
        )
        self.edinburgh_east_post_ballot.election.election_date = "2019-01-01"
        self.edinburgh_east_post_ballot.election.save()
        self.edinburgh_east_post_ballot.election.refresh_from_db()
        self.assertFalse(self.edinburgh_east_post_ballot.polls_closed)

    @mock.patch("django.utils.timezone.now")
    def test_polls_closed_election_earlier_today(self, mock_now):
        mock_now.return_value = timezone.make_aware(
            datetime.datetime(2019, 1, 1, 22, 10, 10)
        )
        self.edinburgh_east_post_ballot.election.election_date = "2019-01-01"
        self.edinburgh_east_post_ballot.election.save()
        self.edinburgh_east_post_ballot.election.refresh_from_db()
        self.assertTrue(self.edinburgh_east_post_ballot.polls_closed)
