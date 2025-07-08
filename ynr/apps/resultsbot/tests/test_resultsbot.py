from unittest.mock import MagicMock

from candidates.tests.factories import MembershipFactory
from django.conf import settings
from django.contrib.auth.models import User
from django.test import TestCase
from parties.tests.factories import PartyFactory
from people.tests.factories import PersonFactory
from resultsbot.helpers import ResultsBot
from resultsbot.tests.mixins import KirkleesBatleyEastMixin


class ResultsBotAddResultsTest(KirkleesBatleyEastMixin, TestCase):
    def setUp(self):
        super().setUp()
        self.user = User.objects.create_user(
            username=settings.RESULTS_BOT_USERNAME
        )
        # mock ModGovdivision
        self.division = MagicMock()
        self.division.local_area = self.batley_east_ballot
        self.division.spoiled_votes = 0
        self.division.turnout_percentage = 50
        self.division.numballotpapersissued = 100
        self.division.electorate = 200

        self.bot = ResultsBot()

    def create_candidate_list(self, votes: list):
        """
        Creates a list of Mock ModGovCandidate objects from a list of votes.
        """
        candidate_list = []
        for i in range(len(votes)):
            candidate = MagicMock()
            candidate.votes = votes[i]
            candidate.ynr_membership = MembershipFactory(
                ballot=self.batley_east_ballot,
                person=PersonFactory(),
                party=PartyFactory(),
            )
            candidate_list.append(candidate)
        return candidate_list

    def test_add_results_basic(self):
        self.bot.add_results(
            division=self.division,
            candidate_list=self.create_candidate_list(votes=[50, 30, 0]),
            source="test_source",
        )

        self.assertEqual(
            self.batley_east_ballot.resultset.candidate_results.count(), 3
        )

    def test_add_results_tied_losers(self):
        self.bot.add_results(
            division=self.division,
            candidate_list=self.create_candidate_list(votes=[10, 0, 0]),
            source="test_source",
        )

        self.assertEqual(
            self.batley_east_ballot.resultset.candidate_results.count(), 3
        )

    def test_add_results_tied_winners(self):
        self.bot.add_results(
            division=self.division,
            candidate_list=self.create_candidate_list(votes=[10, 10]),
            source="test_source",
        )

        # Result set is created, but candidate results are not
        self.assertTrue(hasattr(self.batley_east_ballot, "resultset"))
        self.assertEqual(
            self.batley_east_ballot.resultset.candidate_results.count(), 0
        )

    def test_add_results_tied_winners_multiple_seats_contested(self):
        self.batley_east_ballot.winner_count = 2
        self.batley_east_ballot.save()

        self.bot.add_results(
            division=self.division,
            candidate_list=self.create_candidate_list(votes=[30, 20, 20, 10]),
            source="test_source",
        )

        # Result set is created, but candidate results are not
        self.assertTrue(hasattr(self.batley_east_ballot, "resultset"))
        self.assertEqual(
            self.batley_east_ballot.resultset.candidate_results.count(), 0
        )

    def test_add_results_tied_losers_multiple_seats_contested(self):
        self.batley_east_ballot.winner_count = 2
        self.batley_east_ballot.save()

        self.bot.add_results(
            division=self.division,
            candidate_list=self.create_candidate_list(votes=[30, 20, 10, 10]),
            source="test_source",
        )

        self.assertEqual(
            self.batley_east_ballot.resultset.candidate_results.count(), 4
        )
