from django_webtest import WebTest

import people.tests.factories
from people.models import Person

from candidates.tests import factories
from candidates.tests.auth import TestUserMixin
from candidates.tests.uk_examples import UK2015ExamplesMixin
from candidates.models import Ballot

from uk_results.models import CandidateResult, ResultSet


class TestUKResultsPreserved(TestUserMixin, UK2015ExamplesMixin, WebTest):
    def setUp(self):
        super().setUp()
        self.primary_person = people.tests.factories.PersonFactory.create(
            id="3885", name="Harriet Harman"
        )
        self.secondary_person = people.tests.factories.PersonFactory.create(
            id="10000", name="Harriet Ruth Harman"
        )

    def test_uk_results_for_secondary_preserved(self):
        factories.MembershipFactory.create(
            person=self.primary_person,
            post=self.camberwell_post,
            party=self.labour_party,
            ballot=self.camberwell_post_ballot_earlier,
        )
        factories.MembershipFactory.create(
            person=self.secondary_person,
            post=self.local_post,
            party=self.labour_party,
            ballot=self.local_election.ballot_set.get(post=self.local_post),
        )
        secondary_membership = factories.MembershipFactory.create(
            person=self.secondary_person,
            post=self.camberwell_post,
            party=self.labour_party,
            ballot=self.camberwell_post_ballot,
        )

        # Now attach a vote count to the secondary person's candidacy:

        result_set = ResultSet.objects.create(
            ballot=self.camberwell_post_ballot,
            num_turnout_reported=51561,
            num_spoilt_ballots=42,
            ip_address="127.0.0.1",
        )
        CandidateResult.objects.create(
            result_set=result_set,
            membership=secondary_membership,
            num_ballots=32614,
            is_winner=True,
        )
        # Now try the merge:
        response = self.app.get(
            "/person/3885/update", user=self.user_who_can_merge
        )
        merge_form = response.forms["person-merge"]
        merge_form["other"] = "10000"
        response = merge_form.submit()

        self.assertEqual(CandidateResult.objects.count(), 1)

        # Now reget the original person and her candidacy - check it
        # has a result attached.
        after_merging = Person.objects.get(pk=3885)
        membership = after_merging.memberships.get(
            ballot__election=self.election
        )
        candidate_result = membership.result
        self.assertEqual(candidate_result.num_ballots, 32614)

    def test_uk_results_for_primary_preserved(self):
        primary_membership = factories.MembershipFactory.create(
            person=self.primary_person,
            post=self.camberwell_post,
            party=self.labour_party,
            ballot=self.camberwell_post_ballot_earlier,
        )
        factories.MembershipFactory.create(
            person=self.secondary_person,
            post=self.local_post,
            party=self.labour_party,
            ballot=self.local_election.ballot_set.get(post=self.local_post),
        )
        factories.MembershipFactory.create(
            person=self.secondary_person,
            post=self.camberwell_post,
            party=self.labour_party,
            ballot=self.camberwell_post_ballot,
        )

        # Now attach a vote count to the primary person's candidacy:
        result_set = ResultSet.objects.create(
            ballot=self.camberwell_post_ballot_earlier,
            num_turnout_reported=46659,
            num_spoilt_ballots=42,
            ip_address="127.0.0.1",
        )
        CandidateResult.objects.create(
            result_set=result_set,
            membership=primary_membership,
            num_ballots=27619,
            is_winner=True,
        )
        # Now try the merge:
        response = self.app.get(
            "/person/3885/update", user=self.user_who_can_merge
        )
        merge_form = response.forms["person-merge"]
        merge_form["other"] = "10000"
        response = merge_form.submit()

        self.assertEqual(CandidateResult.objects.count(), 1)

        # Now reget the original person and her candidacy - check it
        # has a result attached.
        after_merging = Person.objects.get(pk=3885)
        membership = after_merging.memberships.get(
            ballot__election=self.earlier_election
        )
        candidate_result = membership.result
        self.assertEqual(candidate_result.num_ballots, 27619)
