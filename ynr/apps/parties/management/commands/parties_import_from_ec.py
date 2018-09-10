from django.core.management.base import BaseCommand

from parties.importer import ECPartyImporter
from parties.models import PartyEmblem


class Command(BaseCommand):
    help = """
    Import policital parties that can stand candidates from The Electoral 
    Commission's API in to the Parties app.
    
    
    This command creates 3 types of object: parties, descriptions and emblems.
    
    It also creates joint parties. That is, a psudo-party that allows us to 
    mark candidates as standing for 2 parties.  
    """

    def add_arguments(self, parser):
        parser.add_argument(
            "--clear-emblems",
            action="store_true",
            help="Deletes all emblems and re-downloads them all",
        )
        parser.add_argument(
            "--output-new-parties",
            action="store_true",
            help="Write newly created parties to stdout (helpful for notifying of newly registererd parties)",
        )
        parser.add_argument(
            "--skip-create-joint",
            action="store_true",
            help="Don't make psudo-parties from joint descriptions",
        )

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
