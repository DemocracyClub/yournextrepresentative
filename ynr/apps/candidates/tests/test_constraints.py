from mock import patch

from django.test import TestCase
from popolo.models import Membership, Post

from elections.models import Election

from candidates.models import (
    check_paired_models,
    check_membership_elections_consistent,
)
from candidates.models.constraints import check_no_candidancy_for_election
from .factories import ElectionFactory, MembershipFactory, PersonFactory
from .uk_examples import UK2015ExamplesMixin


class PairedConstraintCheckTests(UK2015ExamplesMixin, TestCase):
    def test_no_problems_normally(self):
        errors = check_paired_models()
        for e in errors:
            print(e)
        self.assertEqual(0, len(errors))


class PostElectionCombinationTests(UK2015ExamplesMixin, TestCase):
    def test_relationship_ok(self):
        new_candidate = PersonFactory.create(name="John Doe")
        post = Post.objects.get(slug="14419")
        election = Election.objects.get(slug="2015")
        # Create a new candidacy:
        MembershipFactory.create(
            person=new_candidate,
            post=post,
            post_election=election.postextraelection_set.get(post=post),
        )
        self.assertEqual(check_membership_elections_consistent(), [])


class PreventCreatingBadMemberships(UK2015ExamplesMixin, TestCase):
    def test_prevent_creating_conflicts_with_not_standing(self):
        new_candidate = PersonFactory.create(name="John Doe")
        new_candidate.not_standing.add(self.election)

        with self.assertRaisesRegexp(
            Exception,
            r'Trying to add a Membership with an election "2015 '
            r'General Election", but that\'s in John Doe '
            r"\({}\)\'s not_standing list".format(new_candidate.id),
        ):
            Membership.objects.create(
                role="Candidate",
                person=new_candidate,
                party=self.green_party,
                post=self.camberwell_post,
                post_election=self.camberwell_post_pee,
            )

    def test_raise_if_candidacy_exists(self):
        new_candidate = PersonFactory.create(name="John Doe")
        post = Post.objects.get(slug="14419")
        # Create a new candidacy:
        MembershipFactory.create(
            person=new_candidate,
            post=post,
            role=self.election.candidate_membership_role,
            post_election=self.election.postextraelection_set.get(post=post),
        )
        with self.assertRaisesRegexp(
            Exception,
            (
                r"There was an existing candidacy for John Doe "
                r'\({person_id}\) in the election "2015 General '
                r'Election"'
            ).format(person_id=new_candidate.id),
        ):
            check_no_candidancy_for_election(new_candidate, self.election)
