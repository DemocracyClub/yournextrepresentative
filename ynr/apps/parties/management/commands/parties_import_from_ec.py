from io import StringIO

from django.core.management.base import BaseCommand

from parties.importer import ECPartyImporter
from parties.models import PartyEmblem

from utils.slack import SlackHelper


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
            "-q",
            "--quiet",
            action="store_true",
            help="Don't output info about new parties. Will still output on error",
        )
        parser.add_argument(
            "--skip-create-joint",
            action="store_true",
            help="Don't make psudo-parties from joint descriptions",
        )
        parser.add_argument(
            "--post-to-slack",
            action="store_true",
            help="Post to Slack when new parties are found",
        )

    def handle(self, *args, **options):
        if options["quiet"]:
            self.stdout = StringIO()

        if options["clear_emblems"]:
            for emblem in PartyEmblem.objects.all():
                emblem.image.delete()
                emblem.delete()

        importer = ECPartyImporter()
        importer.do_import()

        if not options["skip_create_joint"]:
            importer.create_joint_parties(raise_on_error=False)

        if importer.collector:
            self.stdout.write(
                self.style.SUCCESS(
                    "Found {} new political parties!".format(
                        len(importer.collector)
                    )
                )
            )
            for party in importer.collector:
                self.stdout.write(str(party))

            if options["post_to_slack"]:
                client = SlackHelper()
                if len(importer.collector) == 1:
                    message = "A new party is born!"
                else:
                    message = "{} new political parties have come in to the world!".format(
                        len(importer.collector)
                    )
                client.post_message(
                    "#candidates",
                    message_text=message,
                    attachments=[
                        p.as_slack_attachment for p in importer.collector
                    ],
                )
        else:
            self.stdout.write(
                self.style.SUCCESS("Up do date: No new parties found")
            )

        for error in importer.error_collector:
            self.stderr.write(error)
