from __future__ import unicode_literals

import csv
import os

from django.core.management.base import BaseCommand
from django.db.models import Prefetch

from compat import BufferDictWriter
from uk_results.models import ResultSet
from candidates.models import MembershipExtra


class Command(BaseCommand):
    FIELDNAMES = [
        'election_id',
        'ballot_paper_id',
        'person_id',
        'party_id',
        'party_name',
        'person_name',
        'ballots_cast',
        'is_winner',
    ]


    def add_arguments(self, parser):
        parser.add_argument(
            '--election-date',
            action='store',
            required=True
        )


    def handle(self, **options):
        date = options['election_date']
        qs = ResultSet.objects.filter(
            post_election__election__election_date=date
        ).select_related(
            'post_election',
            'post_election__election',
        ).prefetch_related(
            Prefetch(
                'post_election__membershipextra_set',
                MembershipExtra.objects.select_related(
                    'base',
                    'base__person',
                    'base__on_behalf_of',
                )
            )

        )

        csv_out = BufferDictWriter(fieldnames=self.FIELDNAMES)
        csv_out.writeheader()
        for result in qs:
            row_base = {
                'election_id': result.post_election.election.slug,
                'ballot_paper_id': result.post_election.ballot_paper_id,

            }

            for membership in result.post_election.membershipextra_set.all():
                if not hasattr(membership.base, 'result'):
                    continue
                row = row_base
                party = membership.base.on_behalf_of
                try:
                    if party.name == "Independent":
                        party_id = "ynmp-party:2"
                    else:
                        party_id = party.identifiers.filter(
                            scheme='electoral-commission'
                        ).get().identifier
                except:
                    party_id = ""
                row['party_id'] = party_id
                row['party_name'] = membership.base.on_behalf_of.name
                row['person_id'] = membership.base.person.pk
                row['person_name'] = membership.base.person.name
                row['ballots_cast'] = membership.base.result.num_ballots
                row['is_winner'] = membership.base.result.is_winner
                csv_out.writerow(row)
        self.stdout.write(csv_out.output)
