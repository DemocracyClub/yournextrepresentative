from django.core.management.base import BaseCommand

from moderation_queue.models import QueuedImage


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument(
            "--delete",
            action="store_true",
            help=("Delete moderation queue items with no image"),
        )

    def handle(self, **options):
        qs = QueuedImage.objects.filter(decision="undecided")
        for qi in qs:
            try:
                qi.image.file
            except (ValueError, IOError):
                if options["delete"]:
                    self.stdout.write(
                        "Deleting {} because it has no image".format(qi)
                    )
                    qi.delete()
                else:
                    self.stdout.write("{} has no image".format(qi))
