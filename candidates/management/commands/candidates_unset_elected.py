from __future__ import print_function, unicode_literals

from datetime import date

from django.core.management.base import BaseCommand, CommandError

from candidates.models import MembershipExtra
from elections.models import Election


class Command(BaseCommand):

    def add_arguments(self, parser):
        parser.add_argument(
            'ELECTION-ID',
            help='The ID of the election for which to reset all candidacy elected statuses'
        )
        parser.add_argument(
            '-f', '--force',
            action='store_true',
            help='Unset the candidacy elected status even if the election is in the past'
        )

    def handle(self, **options):
        election_slug = options['ELECTION-ID']
        election = Election.objects.get(slug=election_slug)
        if election.election_date <= date.today() and not options['force']:
            msg = "The election {0.name} ({0.slug}) is in the past: run with " \
                  "-f if you really want to do this"
            raise CommandError(msg.format(election))
        MembershipExtra.objects.filter(election=election) \
            .update(elected=None)
