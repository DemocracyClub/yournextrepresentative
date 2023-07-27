from candidates.models.constraints import check_no_candidancy_for_election
from django.test import TestCase
from people.tests.factories import PersonFactory
from popolo.models import Post

from .factories import MembershipFactory
from .uk_examples import UK2015ExamplesMixin


class PreventCreatingBadMemberships(UK2015ExamplesMixin, TestCase):
    def test_raise_if_candidacy_exists(self):
        new_candidate = PersonFactory.create(name="John Doe")
        post = Post.objects.get(slug="14419")
        # Create a new candidacy:
        MembershipFactory.create(
            person=new_candidate,
            post=post,
            ballot=self.election.ballot_set.get(post=post),
            party=self.labour_party,
        )
        with self.assertRaisesRegex(
            Exception,
            (
                r"There was an existing candidacy for John Doe "
                r'\({person_id}\) in the election "2015 General '
                r'Election"'
            ).format(person_id=new_candidate.id),
        ):
            check_no_candidancy_for_election(new_candidate, self.election)
