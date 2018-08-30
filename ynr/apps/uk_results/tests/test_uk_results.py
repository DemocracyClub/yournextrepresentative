from django.test import TestCase

from candidates.tests.auth import TestUserMixin
from candidates.tests.factories import MembershipFactory, PersonFactory
from candidates.tests.uk_examples import UK2015ExamplesMixin
from uk_results.models import CandidateResult, ResultSet


class TestUKResults(TestUserMixin, UK2015ExamplesMixin, TestCase):
    def setUp(self):
        super().setUp()
        pee = self.local_post.postextraelection_set.get()
        self.result_set = ResultSet.objects.create(
            post_election=pee,
            num_turnout_reported=10000,
            num_spoilt_ballots=30,
            user=self.user,
            ip_address="127.0.0.1",
            source="Example ResultSet for testing",
        )
        # Create three people:
        self.persons = [
            PersonFactory.create(id="13", name="Alice"),
            PersonFactory.create(id="14", name="Bob"),
            PersonFactory.create(id="15", name="Carol"),
        ]

        parties_extra = [
            self.labour_party_extra,
            self.conservative_party_extra,
            self.ld_party_extra,
        ]
        # Create their candidacies:
        candidacies = [
            MembershipFactory.create(
                post_election=pee,
                person=person,
                post=self.local_post,
                on_behalf_of=party_extra.base,
            )
            for person, party_extra in zip(self.persons, parties_extra)
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
            "created": self.result_set.created.isoformat(),
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
            "user": "john",
        }

    def test_as_dict(self):
        self.maxDiff = None
        self.assertEqual(self.result_set.as_dict(), self.expected)

    def test_record_version(self):
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
        self.assertEqual(
            self.result_set.versions, [self.expected, self.expected]
        )

        self.result_set.num_turnout_reported = 300
        self.result_set.save()
        self.result_set.record_version()
