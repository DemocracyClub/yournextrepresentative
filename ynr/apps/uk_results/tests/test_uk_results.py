from candidates.models import LoggedAction
from candidates.tests.auth import TestUserMixin
from candidates.tests.factories import MembershipFactory
from candidates.tests.uk_examples import UK2015ExamplesMixin
from django.test import TestCase
from django_webtest import WebTest
from people.tests.factories import PersonFactory
from popolo.models import Membership
from uk_results.models import CandidateResult, ResultSet, SuggestedWinner


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
        elected = [False, True, False]

        self.candidate_results = []
        for c, v, e in zip(candidacies, votes, elected):
            c.elected = e
            c.save()
            result = CandidateResult.objects.create(
                result_set=self.result_set, membership=c, num_ballots=v
            )
            self.candidate_results.append(result)

        self.expected = {
            "ballot_paper_id": "local.maidstone.DIW:E05005004.2016-05-05",
            "created": self.result_set.modified.isoformat(),
            "candidate_results": [
                {
                    "elected": True,
                    "num_ballots": 5000,
                    "person_id": 14,
                    "person_name": "Bob",
                },
                {
                    "elected": False,
                    "num_ballots": 3000,
                    "person_id": 15,
                    "person_name": "Carol",
                },
                {
                    "elected": False,
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
        self.assertEqual(self.result_set.turnout_percentage, 33)

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

    def test_suggesting_votes(self):
        ballot = self.local_post.ballot_set.get()
        ballot.membership_set.update(elected=False)
        membership = ballot.membership_set.first()
        self.assertFalse(membership.elected)

        # Suggest a winner. We expect this to do nothing other than record this fact
        SuggestedWinner.record_suggestion(
            user=self.user, membership=membership, is_elected=True
        )

        # The winner is not set
        membership.refresh_from_db()
        self.assertFalse(membership.elected)

        # A different person suggests the same winner
        # The actual user doesn't matter here, as long as it's different to the first one
        SuggestedWinner.record_suggestion(
            user=self.user_who_can_lock, membership=membership, is_elected=True
        )

        # Membership is elected
        membership.refresh_from_db()
        self.assertTrue(membership.elected)

        # First user made a mistake, suggests not elected
        SuggestedWinner.record_suggestion(
            user=self.user, membership=membership, is_elected=False
        )

        # The winner is not set
        membership.refresh_from_db()
        self.assertFalse(membership.elected)

    def test_suggesting_votes_existing_winners(self):
        ballot = self.local_post.ballot_set.get()
        membership, other_membership = ballot.membership_set.all()[:2]

        self.assertTrue(membership.elected)
        self.assertFalse(other_membership.elected)

        SuggestedWinner.record_suggestion(
            user=self.user_who_can_lock,
            membership=other_membership,
            is_elected=True,
        )
        # The winner is not set
        other_membership.refresh_from_db()
        self.assertFalse(other_membership.elected)
        SuggestedWinner.record_suggestion(
            user=self.user, membership=other_membership, is_elected=True
        )
        # The winner is not set
        other_membership.refresh_from_db()
        self.assertFalse(other_membership.elected)

    def test_suggesting_votes_initial_mistake(self):
        ballot = self.local_post.ballot_set.get()
        ballot.membership_set.update(elected=False)
        membership, other_membership = ballot.membership_set.all()[:2]

        self.assertFalse(membership.elected)
        self.assertFalse(other_membership.elected)

        SuggestedWinner.record_suggestion(
            user=self.user_who_can_lock,
            membership=other_membership,
            is_elected=True,
        )
        # The winner is not set
        self.assertFalse(ballot.membership_set.filter(elected=True).exists())

        SuggestedWinner.record_suggestion(
            user=self.user_who_can_lock, membership=membership, is_elected=True
        )
        # The winner is not set
        self.assertFalse(ballot.membership_set.filter(elected=True).exists())

        SuggestedWinner.record_suggestion(
            user=self.user, membership=membership, is_elected=True
        )
        # We now elect the person
        membership.refresh_from_db()
        self.assertTrue(membership.elected)


class TestGEMarkWinnerFrontend(
    TestUserMixin, UK2015ExamplesMixin, WebTest, TestCase
):
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
        elected = [False, True, False]

        self.candidate_results = []
        for c, v, e in zip(candidacies, votes, elected):
            c.elected = e
            c.save()
            result = CandidateResult.objects.create(
                result_set=self.result_set, membership=c, num_ballots=v
            )
            self.candidate_results.append(result)

        self.expected = {
            "ballot_paper_id": "local.maidstone.DIW:E05005004.2016-05-05",
            "created": self.result_set.modified.isoformat(),
            "candidate_results": [
                {
                    "elected": True,
                    "num_ballots": 5000,
                    "person_id": 14,
                    "person_name": "Bob",
                },
                {
                    "elected": False,
                    "num_ballots": 3000,
                    "person_id": 15,
                    "person_name": "Carol",
                },
                {
                    "elected": False,
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

        self.local_election.slug = "parl.2024-07-04"
        self.local_election.save()
        self.local_election.ballot_set.first().membership_set.update(
            elected=False
        )

    def test_mark_winners(self):
        ballot = self.local_post.ballot_set.get()

        ballot.membership_set.update(elected=False)

        self.assertFalse(Membership.objects.filter(elected=True).exists())

        response = self.app.get("/uk_results/parl.2024-07-04/", user=self.user)
        form = response.forms["localmaidstonediwe050050042016-05-05"]

        form["membership_id"] = form["membership_id"].options[0][0]
        form.submit()

        self.assertFalse(Membership.objects.filter(elected=True).exists())

        # Same user does the same action again, winner not marked
        response = self.app.get("/uk_results/parl.2024-07-04/", user=self.user)
        form = response.forms["localmaidstonediwe050050042016-05-05"]
        form["membership_id"] = form["membership_id"].options[0][0]
        form.submit()

        self.assertFalse(Membership.objects.filter(elected=True).exists())

        # Same user does the same action again, winner not marked
        response = self.app.get(
            "/uk_results/parl.2024-07-04/",
            user=self.user_who_can_record_results,
        )
        form = response.forms["localmaidstonediwe050050042016-05-05"]
        form["membership_id"] = form["membership_id"].options[0][0]
        form.submit()

        self.assertTrue(Membership.objects.filter(elected=True).exists())

        # Same user made a mistake
        response = self.app.get(
            "/uk_results/parl.2024-07-04/",
            user=self.user_who_can_record_results,
        )
        form = response.forms["localmaidstonediwe050050042016-05-05"]
        form["unset"] = "1"
        form.submit()

        self.assertFalse(Membership.objects.filter(elected=True).exists())

        self.assertEqual(LoggedAction.objects.count(), 4)
        self.assertEqual(
            list(LoggedAction.objects.values_list("action_type", flat=True)),
            [
                "entered-results-data",
                "entered-results-data",
                "set-candidate-elected",
                "retract-winner",
            ],
        )
