from django.test import TestCase
from django.urls import reverse
from django_webtest import WebTest
from candidates.models.popolo_extra import Ballot

from candidates.tests.auth import TestUserMixin
from candidates.tests.factories import MembershipFactory
from candidates.tests.uk_examples import UK2015ExamplesMixin
from people.tests.factories import PersonFactory
from uk_results.models import CandidateResult, ResultSet


class TestUKResults(TestUserMixin, UK2015ExamplesMixin, WebTest, TestCase):
    def setUp(self):
        super().setUp()
        self.ballot = self.local_post.ballot_set.get()
        self.ballot.voting_system = Ballot.VOTING_SYSTEM_FPTP
        self.ballot.save()
        self.result_set = ResultSet.objects.create(
            ballot=self.ballot,
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
                ballot=self.ballot,
                person=person,
                post=self.local_post,
                party=party,
            )
            for person, party in zip(self.people, parties)
        ]
        # Create their CandidateResult objects:
        votes = [2000, 5000, 3000]
        self.candidate_results = [
            CandidateResult.objects.create(
                result_set=self.result_set, membership=c, num_ballots=v
            )
            for c, v in zip(candidacies, votes)
        ]

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
        self.ballot.cancelled = True
        self.ballot.save()
        resp = self.app.get(
            url, user=self.user_who_can_record_results, expect_errors=True
        )
        self.assertEqual(resp.status_code, 404)
