from __future__ import print_function, unicode_literals

from mock import patch

from django.test import TestCase

from candidates.tests.auth import TestUserMixin
from candidates.tests.factories import (
    CandidacyExtraFactory, PersonExtraFactory)
from candidates.tests.uk_examples import UK2015ExamplesMixin

from results.models import ResultEvent

from .models import CandidateResult, PostElectionResult, ResultSet
from .forms import mark_candidates_as_winner


class TestUKResults(TestUserMixin, UK2015ExamplesMixin, TestCase):

    def setUp(self):
        super(TestUKResults, self).setUp()
        # Create a PostElectionResult, initially not confirmed.
        pee = self.local_post.postextraelection_set.get()
        per = PostElectionResult.objects.create(
            post_election=pee,
            confirmed=False,
        )
        # Now create a ResultSet
        self.result_set = ResultSet.objects.create(
            post_election_result=per,
            num_turnout_reported=10000,
            num_spoilt_ballots=30,
            user=self.user,
            ip_address='127.0.0.1',
            source='Example ResultSet for testing',
            reviewed_by=self.user_who_can_record_results,
        )
        # Create three people:
        self.persons_extra = [
            PersonExtraFactory.create(base__id='13', base__name='Alice'),
            PersonExtraFactory.create(base__id='14', base__name='Bob'),
            PersonExtraFactory.create(base__id='15', base__name='Carol'),
        ]
        parties_extra = [
            self.labour_party_extra,
            self.conservative_party_extra,
            self.ld_party_extra
        ]
        # Create their candidacies:
        candidacies = [
            CandidacyExtraFactory.create(
                election=self.local_election,
                base__person=person_extra.base,
                base__post=self.local_post.base,
                base__on_behalf_of=party_extra.base,
            ).base
            for person_extra, party_extra
            in zip(self.persons_extra, parties_extra)
        ]
        # Create their CandidateResult objects:
        votes = [2000, 5000, 3000]
        winner = [False, True, False]
        self.candidate_results = [
            CandidateResult.objects.create(
                result_set=self.result_set,
                membership=c,
                num_ballots_reported=v,
                is_winner=w)
            for c, v, w in zip(candidacies, votes, winner)
        ]
        # Now make that the confirmed ResultSet for that
        # PostElectionResult.
        per.confirmed = True
        per.confirmed_resultset = self.result_set
        per.save()

    @patch('uk_results.forms.get_change_metadata')
    def test_mark_candidates_as_winner(self, mock_get_change_metadata):
        # 'instance' here is an instance of ResultSet. request is only
        # needed to calculate change_metadata, so patch
        # get_change_metadata instead.
        mock_get_change_metadata.return_value = {
            'information_source': 'Example source for tests',
            'version_id': '277bb23c148bea2c',
            'timestamp': '2017-06-05T14:01:14.394447'
        }
        mark_candidates_as_winner(None, self.result_set)
        self.assertEqual(1, ResultEvent.objects.count())
        result_event = ResultEvent.objects.get()
        self.assertEqual(result_event.election, self.local_election)
        self.assertEqual(result_event.winner, self.persons_extra[1].base)
        self.assertEqual(result_event.post, self.local_post.base)
        self.assertEqual(result_event.winner_party, self.conservative_party_extra.base)
        self.assertEqual(result_event.source, 'Example ResultSet for testing')
        self.assertEqual(result_event.user, self.user_who_can_record_results)
