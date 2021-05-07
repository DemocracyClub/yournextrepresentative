from django.test import TestCase

from candidates.tests.auth import TestUserMixin
from candidates.tests.factories import MembershipFactory
from candidates.tests.uk_examples import UK2015ExamplesMixin
from people.tests.factories import PersonFactory
from uk_results.models import CandidateResult, ResultSet


class TestUKResults(TestUserMixin, UK2015ExamplesMixin, TestCase):
    def setUp(self):
        super().setUp()
        ballot = self.local_post.ballot_set.get()
        self.result_set = ResultSet.objects.create(
            ballot=ballot,
            num_turnout_reported=10000,
            num_spoilt_ballots=30,
            user=self.user,
            ip_address="127.0.0.1",
            source="Example ResultSet for testing",
            total_electorate=50000,
        )
        # Create three people:
        self.persons = [
            PersonFactory.create(id=13, name="Alice"),
            PersonFactory.create(id=14, name="Bob"),
            PersonFactory.create(id=15, name="Carol"),
        ]

        parties = [self.labour_party, self.conservative_party, self.ld_party]
        # Create their candidacies:
        candidacies = [
            MembershipFactory.create(
                ballot=ballot, person=person, post=self.local_post, party=party
            )
            for person, party in zip(self.persons, parties)
        ]
        # Create their CandidateResult objects:
        votes = [2000, 5000, 3000]
        winner = [False, True, False]
        self.candidate_results = [
            CandidateResult.objects.create(
                result_set=self.result_set,
                membership=c,
                num_ballots=v,
                is_winner=w,
            )
            for c, v, w in zip(candidacies, votes, winner)
        ]

        self.expected = {
            "ballot_paper_id": "local.maidstone.DIW:E05005004.2016-05-05",
            "created": self.result_set.modified.isoformat(),
            "candidate_results": [
                {
                    "is_winner": True,
                    "num_ballots": 5000,
                    "person_id": 14,
                    "person_name": "Bob",
                },
                {
                    "is_winner": False,
                    "num_ballots": 3000,
                    "person_id": 15,
                    "person_name": "Carol",
                },
                {
                    "is_winner": False,
                    "num_ballots": 2000,
                    "person_id": 13,
                    "person_name": "Alice",
                },
            ],
            "source": "Example ResultSet for testing",
            "spoilt_ballots": 30,
            "turnout": 10000,
            "total_electorate": 50000,
            "user": "john",
        }

    def test_as_dict(self):
        self.maxDiff = None
        self.assertEqual(self.result_set.as_dict(), self.expected)

    def test_record_version(self):
        self.maxDiff = None
        self.assertEqual(self.result_set.versions, [])
        self.result_set.record_version()
        self.assertEqual(self.result_set.versions, [self.expected])

        # Make sure we don't create duplicate versons
        self.result_set.record_version()
        self.result_set.record_version()
        self.assertEqual(self.result_set.versions, [self.expected])

        # Make sure we can force a duplicate though
        self.result_set.record_version(force=True)
        self.assertEqual(len(self.result_set.versions), 2)
        self.assertTrue(
            self.result_set.versions_equal(
                self.result_set.versions[0], self.result_set.versions[1]
            )
        )

        self.result_set.num_turnout_reported = 300
        self.result_set.save()
        self.result_set.record_version()

    def test_turnout_percentage(self):
        self.result_set.calculate_turnout_percentage()
        self.assertEqual(self.result_set.turnout_percentage, 20.0)
        self.result_set.num_turnout_reported = 3333
        self.result_set.total_electorate = 10000
        self.result_set.calculate_turnout_percentage()
        # check rounded to 2 places max
        self.assertEqual(self.result_set.turnout_percentage, 33.33)

    def test_turnout_percentage_is_none(self):
        results = [
            ResultSet(num_turnout_reported=None, total_electorate=None),
            ResultSet(num_turnout_reported=5000, total_electorate=None),
            ResultSet(num_turnout_reported=None, total_electorate=5000),
        ]
        for result in results:
            with self.subTest(msg=result):
                result.calculate_turnout_percentage()
                self.assertIsNone(result.turnout_percentage)

    def test_turnout_percentage_max_100(self):
        result = ResultSet(num_turnout_reported=100, total_electorate=50)
        result.calculate_turnout_percentage()
        self.assertEqual(result.turnout_percentage, 100)
