from __future__ import print_function, unicode_literals

from mock import patch

from django.test import TestCase

from candidates.tests.auth import TestUserMixin
from candidates.tests.factories import (
    CandidacyExtraFactory, PersonExtraFactory)
from candidates.tests.uk_examples import UK2015ExamplesMixin

from results.models import ResultEvent

from uk_results.models import CandidateResult, ResultSet


class TestUKResults(TestUserMixin, UK2015ExamplesMixin, TestCase):

    def setUp(self):
        super(TestUKResults, self).setUp()
        pee = self.local_post.postextraelection_set.get()
        self.result_set = ResultSet.objects.create(
            post_election=pee,
            num_turnout_reported=10000,
            num_spoilt_ballots=30,
            user=self.user,
            ip_address='127.0.0.1',
            source='Example ResultSet for testing',
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
                post_election=pee,
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
                num_ballots=v,
                is_winner=w)
            for c, v, w in zip(candidacies, votes, winner)
        ]
