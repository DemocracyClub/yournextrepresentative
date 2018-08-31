from django.core.management.base import BaseCommand

from parties.importer import ECPartyImporter
from parties.models import PartyEmblem


class Command(BaseCommand):
    help = "My shiny new management command."

    def add_arguments(self, parser):
        parser.add_argument("--clear-emblems", action="store_true")
        parser.add_argument("--output-new-parties", action="store_true")

    def handle(self, *args, **options):
        if options["clear_emblems"]:
            for emblem in PartyEmblem.objects.all():
                emblem.image.delete()
                emblem.delete()

        importer = ECPartyImporter()

        new_parties = importer.do_import()

        if options["output_new_parties"] and new_parties:
            self.stdout.write("Found new political parties!")
            for party in new_parties:
                self.stdout.write(str(party))
