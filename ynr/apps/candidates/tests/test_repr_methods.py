from django.test import TestCase

from .uk_examples import UK2015ExamplesMixin


class TestReprMethods(UK2015ExamplesMixin, TestCase):
    def test_logged_action_repr(self):
        ballot = self.camberwell_post.ballot_set.get(election=self.election)
        self.assertEqual(
            str(ballot),
            "<Ballot ballot_paper_id='parl.65913.2015-05-07' winner_count=1>",
        )

    def test_logged_action_repr_locked_with_winner_count(self):
        ballot = self.camberwell_post.ballot_set.get(election=self.election)
        ballot.winner_count = 4
        ballot.candidates_locked = True
        ballot.save()
        self.assertEqual(
            str(ballot),
            "<Ballot ballot_paper_id='parl.65913.2015-05-07' candidates_locked=True winner_count=4>",
        )
