from django.test import TestCase

from candidates.tests.auth import TestUserMixin
from candidates.tests.uk_examples import UK2015ExamplesMixin
from people.tests.factories import PersonFactory
from results.models import ResultEvent
from candidates.tests.dates import date_in_near_past, date_in_near_future
from uk_results.helpers import RecordBallotResultsHelper


class TestUKResults(TestUserMixin, UK2015ExamplesMixin, TestCase):
    def setUp(self):
        self.local_ballot.election.election_date = date_in_near_past
        self.local_ballot.election.save()
        self.local_ballot.save()

    def test_can_set_winners_polls_not_closed(self):
        recorder = RecordBallotResultsHelper(self.local_ballot, self.user)
        self.local_ballot.election.election_date = date_in_near_future
        with self.assertRaises(ValueError) as exception:
            assert recorder.can_mark_elected
        self.assertEqual(
            str(exception.exception), "Can't set winners until polls are closed"
        )

    def test_can_set_winners_max_winners(self):
        person = PersonFactory()
        self.local_ballot.membership_set.create(
            person=person,
            party=self.green_party,
            ballot=self.local_ballot,
            elected=True,
        )
        recorder = RecordBallotResultsHelper(self.local_ballot, self.user)
        with self.assertRaises(ValueError) as exception:
            assert recorder.can_mark_elected
        self.assertEqual(
            str(exception.exception),
            "There were already 1 winners for "
            "local.maidstone.DIW:E05005004.2016-05-05 and the maximum is 1",
        )

    def test_mark_person_as_elected(self):
        self.assertEqual(ResultEvent.objects.all().count(), 0)
        recorder = RecordBallotResultsHelper(self.local_ballot, self.user)
        person = PersonFactory()
        candidacy = self.local_ballot.membership_set.create(
            person=person,
            party=self.green_party,
            ballot=self.local_ballot,
            elected=False,
        )
        recorder.mark_person_as_elected(person, "Made up")
        self.assertTrue(self.local_ballot.has_results)
        self.assertEqual(ResultEvent.objects.all().count(), 1)
        candidacy.refresh_from_db()
        self.assertTrue(candidacy.elected)
