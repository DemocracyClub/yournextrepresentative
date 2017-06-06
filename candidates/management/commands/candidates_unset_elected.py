from __future__ import print_function, unicode_literals

from django.core.management.base import BaseCommand

from candidates.models import MembershipExtra
from elections.models import Election


class Command(BaseCommand):

    def add_arguments(self, parser):
        parser.add_argument(
            'ELECTION-ID',
            help='The ID of the election for which to reset all candidacy elected statuses'
        )

    def handle(self, **options):
        election_slug = options['ELECTION-ID']
        election = Election.objects.get(slug=election_slug)
        MembershipExtra.objects.filter(election=election) \
            .update(elected=None)
