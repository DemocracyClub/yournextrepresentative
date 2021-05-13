from django import forms
from django.test import TestCase
from django.test.client import RequestFactory
from django_webtest import WebTest

from candidates.tests.auth import TestUserMixin
from candidates.tests.factories import MembershipFactory
from candidates.tests.uk_examples import UK2015ExamplesMixin
from people.tests.factories import PersonFactory
from uk_results.forms import ResultSetForm


class TestResultSetForm(TestUserMixin, UK2015ExamplesMixin, WebTest, TestCase):
    def setUp(self):
        super().setUp()
        self.ballot = self.local_post.ballot_set.get()

        # Create three people:
        self.people = [
            PersonFactory.create(id=13, name="Alice"),
            PersonFactory.create(id=14, name="Bob"),
            PersonFactory.create(id=15, name="Carol"),
        ]

        parties = [self.labour_party, self.conservative_party, self.ld_party]
        # Create their candidacies:
        self.candidacies = [
            MembershipFactory.create(
                ballot=self.ballot,
                person=person,
                post=self.local_post,
                party=party,
            )
            for person, party in zip(self.people, parties)
        ]
        self.rf = RequestFactory()
        self.request = self.rf.get("/")
        self.request.user = self.user_who_can_record_results

    def build_fieldname(self, obj):
        return f"memberships_{obj.person.pk}"

    def test_clean(self):
        """
        Test that you cant have more tied vote winners than number of winners
        for the ballot
        """
        form = ResultSetForm(ballot=self.ballot)
        self.assertEqual(self.ballot.winner_count, 1)
        cleaned_data = {}
        for candidacy in self.candidacies:
            cleaned_data[f"tied_vote_memberships_{candidacy.pk}"] = True

        form.cleaned_data = cleaned_data
        with self.assertRaises(forms.ValidationError) as e:
            form.clean()
            self.assertEqual(
                str(e), "Cant have more coin toss winners than seats up!"
            )

    def test_clean_winner_count_none(self):
        """
        If we dont know the winner count, dont validate it against the tied vote winners
        """
        self.ballot.winner_count = None
        form = ResultSetForm(ballot=self.ballot)
        cleaned_data = {}
        for candidacy in self.candidacies:
            cleaned_data[f"tied_vote_memberships_{candidacy.pk}"] = True

        form.cleaned_data = cleaned_data
        self.assertEqual(form.clean(), cleaned_data)

    def test_tied_vote_winners(self):
        form = ResultSetForm(ballot=self.ballot)
        cleaned_data = {}
        for candidacy in self.candidacies:
            cleaned_data[f"tied_vote_memberships_{candidacy.pk}"] = False

        form.cleaned_data = cleaned_data
        self.assertEqual(form._tied_vote_winners, [])

        # change one to be a vote winner
        candidate = self.candidacies[0]
        cleaned_data[f"tied_vote_memberships_{candidate.pk}"] = True
        form.cleaned_data = cleaned_data

        self.assertEqual(
            form._tied_vote_winners, [f"tied_vote_memberships_{candidate.pk}"]
        )

    def test_get_winners_different_votes(self):
        """
        Test that when all candidates have different number of votes, highest
        votes wins
        """
        votes = 10
        cleaned_data = {"source": "example"}
        for candidate in self.candidacies:
            cleaned_data[f"memberships_{candidate.person.pk}"] = votes
            cleaned_data[f"tied_vote_memberships_{candidate.person.pk}"] = False
            votes += 10

        form = ResultSetForm(data=cleaned_data, ballot=self.ballot)
        self.assertTrue(form.is_valid())

        # expect person with PK 15 to be the winner
        result = form.get_winners()
        self.assertEqual(len(result), 1)
        self.assertEqual(result, {"memberships_15": 30})

        # save and do more checks
        form.save(request=self.request)
        for candidacy in self.candidacies:
            candidacy.refresh_from_db()
        self.assertFalse(self.candidacies[0].elected)
        self.assertFalse(self.candidacies[1].elected)
        self.assertFalse(self.candidacies[1].result.tied_vote_winner)
        self.assertTrue(self.candidacies[2].elected)
        self.assertFalse(self.candidacies[2].result.tied_vote_winner)

    def test_get_winners_different_votes_two_winners(self):
        """
        Test that when all candidates have different number of votes, and ballot
        has two seats up, two highest votes win
        """
        self.ballot.winner_count = 2

        votes = 10
        cleaned_data = {"source": "example"}
        for candidate in self.candidacies:
            cleaned_data[f"memberships_{candidate.person.pk}"] = votes
            cleaned_data[f"tied_vote_memberships_{candidate.person.pk}"] = False
            votes += 10

        form = ResultSetForm(data=cleaned_data, ballot=self.ballot)
        self.assertTrue(form.is_valid())

        # expect person with PK 14 and 15 to be the winners
        result = form.get_winners()
        expected = {"memberships_14": 20, "memberships_15": 30}
        self.assertEqual(len(result), 2)
        self.assertEqual(result, expected)

        # save and do more checks
        form.save(request=self.request)
        for candidacy in self.candidacies:
            candidacy.refresh_from_db()
        self.assertFalse(self.candidacies[0].elected)
        self.assertTrue(self.candidacies[1].elected)
        self.assertFalse(self.candidacies[1].result.tied_vote_winner)
        self.assertTrue(self.candidacies[2].elected)
        self.assertFalse(self.candidacies[2].result.tied_vote_winner)

    def test_get_winners_by_tied_result(self):
        """
        Test that when all candidates have different number of votes, highest
        votes wins
        """
        cleaned_data = {"source": "example"}
        loser_1, loser_2, winner = self.candidacies

        cleaned_data[f"memberships_{loser_1.person.pk}"] = 10
        cleaned_data[f"memberships_{loser_2.person.pk}"] = 10
        # set the winner as same votes but set tied vote value to True
        cleaned_data[f"memberships_{winner.person.pk}"] = 10
        cleaned_data[f"tied_vote_memberships_{winner.person.pk}"] = True

        form = ResultSetForm(data=cleaned_data, ballot=self.ballot)
        self.assertTrue(form.is_valid())

        result = form.get_winners()
        self.assertEqual(len(result), 1)
        self.assertEqual(result, {f"memberships_{winner.person.pk}": 10})

        # save and do more checks
        form.save(request=self.request)
        for candidacy in self.candidacies:
            candidacy.refresh_from_db()
        self.assertFalse(loser_1.elected)
        self.assertFalse(loser_2.elected)
        self.assertTrue(winner.elected)
        self.assertTrue(winner.result.tied_vote_winner)

    def test_get_winners_by_tied_result_multiple_winners(self):
        """
        Test that when there are multiple winners for the ballot, and all
        results are tied, that two people can win by coin toss
        """
        self.ballot.winner_count = 2
        cleaned_data = {"source": "example"}
        loser, winner_1, winner_2 = self.candidacies

        cleaned_data[f"memberships_{loser.person.pk}"] = 10
        cleaned_data[f"memberships_{winner_1.person.pk}"] = 10
        # set two winners as same votes but set tied vote value to True
        cleaned_data[f"tied_vote_memberships_{winner_1.person.pk}"] = True
        cleaned_data[f"memberships_{winner_2.person.pk}"] = 10
        cleaned_data[f"tied_vote_memberships_{winner_2.person.pk}"] = True

        form = ResultSetForm(data=cleaned_data, ballot=self.ballot)
        self.assertTrue(form.is_valid())

        result = form.get_winners()
        expected = {
            f"memberships_{winner_1.person.pk}": 10,
            f"memberships_{winner_2.person.pk}": 10,
        }
        self.assertEqual(len(result), 2)
        self.assertEqual(result, expected)

        # save and do more checks
        form.save(request=self.request)
        for candidacy in self.candidacies:
            candidacy.refresh_from_db()
        self.assertFalse(loser.elected)
        self.assertTrue(winner_1.elected)
        self.assertTrue(winner_1.result.tied_vote_winner)
        self.assertTrue(winner_2.elected)
        self.assertTrue(winner_2.result.tied_vote_winner)
