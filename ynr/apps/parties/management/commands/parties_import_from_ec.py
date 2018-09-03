from django.core.management.base import BaseCommand

from parties.importer import ECPartyImporter
from parties.models import PartyEmblem


class Command(BaseCommand):
    help = "My shiny new management command."

    def add_arguments(self, parser):
        parser.add_argument("--clear-emblems", action="store_true")
        parser.add_argument("--output-new-parties", action="store_true")
        parser.add_argument("--skip-create-joint", action="store_true")

    def handle(self, *args, **options):
        if options["clear_emblems"]:
            for emblem in PartyEmblem.objects.all():
                emblem.image.delete()
                emblem.delete()

        importer = ECPartyImporter()

        importer.do_import()

        if not options["skip_create_joint"]:
            importer.create_joint_parties()

        if options["output_new_parties"] and importer.collector:
            self.stdout.write("Found new political parties!")
            for party in importer.collector:
                self.stdout.write(str(party))
