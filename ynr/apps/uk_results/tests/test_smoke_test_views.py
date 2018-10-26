from django.core.exceptions import ObjectDoesNotExist
from django.core.urlresolvers import reverse
from django.test import TestCase
from django_webtest import WebTest

from candidates.tests.auth import TestUserMixin
from candidates.tests.factories import MembershipFactory, PersonFactory
from candidates.tests.uk_examples import UK2015ExamplesMixin
from uk_results.models import CandidateResult, ResultSet


class TestUKResults(TestUserMixin, UK2015ExamplesMixin, WebTest, TestCase):
    def setUp(self):
        super().setUp()
        self.pee = self.local_post.postextraelection_set.get()
        self.result_set = ResultSet.objects.create(
            post_election=self.pee,
            num_turnout_reported=10000,
            num_spoilt_ballots=30,
            user=self.user,
            ip_address="127.0.0.1",
            source="Example ResultSet for testing",
        )
        # Create three people:
        self.people = [
            PersonFactory.create(id=13, name="Alice"),
            PersonFactory.create(id=14, name="Bob"),
            PersonFactory.create(id=15, name="Carol"),
        ]

        parties = [self.labour_party, self.conservative_party, self.ld_party]
        # Create their candidacies:
        candidacies = [
            MembershipFactory.create(
                post_election=self.pee,
                person=person,
                post=self.local_post,
                party=party,
            )
            for person, party in zip(self.people, parties)
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

    def test_form_view(self):
        url = reverse(
            "ballot_paper_results_form",
            kwargs={
                "ballot_paper_id": "local.maidstone.DIW:E05005004.2016-05-05"
            },
        )
        resp = self.app.get(url, user=self.user_who_can_record_results)
        self.assertEqual(resp.status_code, 200)
        form = resp.forms[1]
        form["memberships_13"] = 345
        form.submit()

    def test_form_view_cancelled_election(self):
        url = reverse(
            "ballot_paper_results_form",
            kwargs={
                "ballot_paper_id": "local.maidstone.DIW:E05005004.2016-05-05"
            },
        )
        self.pee.cancelled = True
        self.pee.save()
        with self.assertRaises(ObjectDoesNotExist):
            resp = self.app.get(url, user=self.user_who_can_record_results)
