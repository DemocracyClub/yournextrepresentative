from django.core.management.base import BaseCommand

from bulk_adding.helpers import CSVImporter
from elections.models import Election


class Command(BaseCommand):
    help = "Create a RawPeople model from a council provided CSV"

    def add_arguments(self, parser):
        parser.add_argument("--file", action="store", required=True)
        parser.add_argument("--election", action="store", required=True)

    def handle(self, *args, **options):
        election = Election.objects.get(slug=options["election"])

        importer = CSVImporter(options["file"], election)

        importer.extract()
