import json
from collections import defaultdict

from django.core.management.base import BaseCommand
from django.db.models import Prefetch

from popolo.models import Membership
from compat import BufferDictWriter
from uk_results.models import ResultSet


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
        'spoilt_ballots',
        'turnout',
        'source',
    ]

    def add_arguments(self, parser):
        parser.add_argument(
            '--election-date',
            action='store',
            required=True
        )

        parser.add_argument(
            '--format',
            action='store',
            required=True,
            choices=['csv', 'json']
        )


    def handle(self, **options):
        date = options['election_date']
        format = options['format']

        qs = ResultSet.objects.filter(
            post_election__election__election_date=date
        ).select_related(
            'post_election',
            'post_election__election',
        ).prefetch_related(
            Prefetch(
                'post_election__membership_set',
                Membership.objects.select_related(
                    'person',
                    'on_behalf_of',
                )
            )

        )
        out_data = []
        for result in qs:

            for membership in result.post_election.membership_set.all():
                if not hasattr(membership, 'result'):
                    continue
                row = {
                    'election_id': result.post_election.election.slug,
                    'ballot_paper_id': result.post_election.ballot_paper_id,
                    'turnout': result.num_turnout_reported,
                    'spoilt_ballots': result.num_spoilt_ballots,
                    'source': result.source,
                }
                party = membership.on_behalf_of
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
                row['party_name'] = membership.on_behalf_of.name
                row['person_id'] = membership.person.pk
                row['person_name'] = membership.person.name
                row['ballots_cast'] = membership.result.num_ballots
                row['is_winner'] = membership.result.is_winner
                out_data.append(row)

        if format == "csv":
            csv_out = BufferDictWriter(fieldnames=self.FIELDNAMES)
            csv_out.writeheader()
            for row in out_data:
                csv_out.writerow(row)
            self.stdout.write(csv_out.output)
        else:
            json_data = defaultdict(dict)
            for person in out_data:
                election_dict = json_data[person['ballot_paper_id']]
                election_dict['turnout'] = person['turnout']
                election_dict['spoilt_ballots'] = person['spoilt_ballots']
                election_dict['source'] = person['source']

                if 'candidates' not in election_dict:
                    election_dict['candidates'] = []
                election_dict['candidates'].append({
                    'person_name': person['person_name'],
                    'person_id': person['person_id'],
                    'party_name': person['party_name'],
                    'party_id': person['party_id'],
                    'ballots_cast': person['ballots_cast'],
                    'is_winner': person['is_winner']
                })
                election_dict['candidates'] = sorted(
                    election_dict['candidates'],
                    key=lambda p: p['ballots_cast'],
                    reverse=True
                )
            self.stdout.write(json.dumps(json_data, indent=4))
