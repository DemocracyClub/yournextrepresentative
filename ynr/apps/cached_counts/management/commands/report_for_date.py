from django.core.management.base import BaseCommand

from cached_counts.report_helpers import report_runner


class Command(BaseCommand):
    help = "My shiny new management command."

    def add_arguments(self, parser):
        parser.add_argument(
            "--date",
            action="store",
            dest="date",
            help="The election date",
            required=True,
        )

        parser.add_argument(
            "--reports",
            action="store",
            dest="reports",
            help="The name of the report(s) to run, comma separated",
            required=True,
        )

    def handle(self, *args, **options):
        for report in options["reports"].split(","):
            report_runner(options["date"], report)
