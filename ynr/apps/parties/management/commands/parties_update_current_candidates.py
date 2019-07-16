from django.core.management.base import BaseCommand

from parties.models import Party


class Command(BaseCommand):
    help = """
    Update the current and total candidates field on the `Party` model
    
    Designed to be run on a cron daily.
    """

    def handle(self, *args, **options):
        parties_qs = Party.objects.all()
        for party in parties_qs:
            party.total_candidates = party.membership_set.count()
            party.current_candidates = party.membership_set.filter(
                ballot__election__current=True
            ).count()
            party.save()
