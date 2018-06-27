from django_webtest import WebTest
from popolo.models import Person

from candidates.tests import factories
from candidates.tests.auth import TestUserMixin
from candidates.tests.uk_examples import UK2015ExamplesMixin
from candidates.models import PostExtraElection

from uk_results.models import CandidateResult, ResultSet


class TestUKResultsPreserved(TestUserMixin, UK2015ExamplesMixin, WebTest):

    def setUp(self):
        super(TestUKResultsPreserved, self).setUp()
        self.primary_person = factories.PersonExtraFactory.create(
            base__id='3885',
            base__name='Harriet Harman'
        ).base
        self.secondary_person = factories.PersonExtraFactory.create(
            base__id='10000',
            base__name='Harriet Ruth Harman',
        ).base

    def test_uk_results_for_secondary_preserved(self):
        factories.MembershipFactory.create(
            person=self.primary_person,
            post=self.camberwell_post_extra.base,
            on_behalf_of=self.labour_party_extra.base,
            post_election=self.camberwell_post_extra_pee_earlier,
        )
        factories.MembershipFactory.create(
            person=self.secondary_person,
            post=self.local_post.base,
            on_behalf_of=self.labour_party_extra.base,
            post_election=self.local_election.postextraelection_set.get(
                postextra=self.local_post
            ),
        )
        secondary_membership = factories.MembershipFactory.create(
            person=self.secondary_person,
            post=self.camberwell_post_extra.base,
            on_behalf_of=self.labour_party_extra.base,
            post_election=self.camberwell_post_extra_pee
        )

        # Now attach a vote count to the secondary person's candidacy:

        result_set = ResultSet.objects.create(
            post_election=self.camberwell_post_extra_pee,
            num_turnout_reported=51561,
            num_spoilt_ballots=42,
            ip_address='127.0.0.1',
        )
        CandidateResult.objects.create(
            result_set=result_set,
            membership=secondary_membership,
            num_ballots=32614,
            is_winner=True,
        )
        # Now try the merge:
        response = self.app.get(
            '/person/3885/update',
            user=self.user_who_can_merge)
        merge_form = response.forms['person-merge']
        merge_form['other'] = '10000'
        response = merge_form.submit()

        self.assertEqual(CandidateResult.objects.count(), 1)

        # Now reget the original person and her candidacy - check it
        # has a result attached.
        after_merging = Person.objects.get(pk=3885)
        membership = after_merging.memberships.get(
            post_election__election=self.election)
        candidate_result = membership.result
        self.assertEqual(candidate_result.num_ballots, 32614)

    def test_uk_results_for_primary_preserved(self):
        primary_membership = factories.MembershipFactory.create(
            person=self.primary_person,
            post=self.camberwell_post_extra.base,
            on_behalf_of=self.labour_party_extra.base,
            post_election=self.camberwell_post_extra_pee_earlier,
        )
        factories.MembershipFactory.create(
            person=self.secondary_person,
            post=self.local_post.base,
            on_behalf_of=self.labour_party_extra.base,
            post_election=self.local_election.postextraelection_set.get(
                postextra=self.local_post
            )
        )
        factories.MembershipFactory.create(
            person=self.secondary_person,
            post=self.camberwell_post_extra.base,
            on_behalf_of=self.labour_party_extra.base,
            post_election=self.camberwell_post_extra_pee,
        )

        # Now attach a vote count to the primary person's candidacy:
        result_set = ResultSet.objects.create(
            post_election=self.camberwell_post_extra_pee_earlier,
            num_turnout_reported=46659,
            num_spoilt_ballots=42,
            ip_address='127.0.0.1',
        )
        CandidateResult.objects.create(
            result_set=result_set,
            membership=primary_membership,
            num_ballots=27619,
            is_winner=True,
        )
        # Now try the merge:
        response = self.app.get(
            '/person/3885/update',
            user=self.user_who_can_merge)
        merge_form = response.forms['person-merge']
        merge_form['other'] = '10000'
        response = merge_form.submit()

        self.assertEqual(CandidateResult.objects.count(), 1)

        # Now reget the original person and her candidacy - check it
        # has a result attached.
        after_merging = Person.objects.get(pk=3885)
        membership = after_merging.memberships.get(
            post_election__election=self.earlier_election)
        candidate_result = membership.result
        self.assertEqual(candidate_result.num_ballots, 27619)
