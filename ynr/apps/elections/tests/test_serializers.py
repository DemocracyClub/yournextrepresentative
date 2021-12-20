from unittest.mock import PropertyMock, patch
from django.test import TestCase
from candidates.tests.factories import BallotPaperFactory

from elections.api.next.serializers import BallotSerializer


class TestBallotSerializerGetCancelled(TestCase):
    def test_when_cancelled(self):
        ballot = BallotPaperFactory(cancelled=True)
        self.assertFalse(ballot.uncontested)
        serializer = BallotSerializer(instance=ballot)
        cancelled = serializer.get_cancelled(instance=ballot)
        self.assertTrue(cancelled)

    def test_when_not_cancelled(self):
        ballot = BallotPaperFactory(cancelled=False)
        self.assertFalse(ballot.uncontested)
        serializer = BallotSerializer(instance=ballot)
        cancelled = serializer.get_cancelled(instance=ballot)
        self.assertFalse(cancelled)

    def test_when_uncontested_not_cancelled(self):
        ballot = BallotPaperFactory(cancelled=False)
        with patch(
            "candidates.models.Ballot.uncontested",
            new_callable=PropertyMock,
            return_value=True,
        ):
            self.assertTrue(ballot.uncontested)
            serializer = BallotSerializer(instance=ballot)
            cancelled = serializer.get_cancelled(instance=ballot)
            self.assertTrue(cancelled)

    def test_when_uncontested_and_cancelled(self):
        ballot = BallotPaperFactory(cancelled=True)
        with patch(
            "candidates.models.Ballot.uncontested",
            new_callable=PropertyMock,
            return_value=True,
        ):
            self.assertTrue(ballot.uncontested)
            serializer = BallotSerializer(instance=ballot)
            cancelled = serializer.get_cancelled(instance=ballot)
            self.assertTrue(cancelled)
