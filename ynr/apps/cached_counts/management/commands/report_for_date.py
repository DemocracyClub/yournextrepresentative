from django.core.management.base import BaseCommand

from cached_counts.report_helpers import report_runner, ALL_REPORT_CLASSES


class Command(BaseCommand):
    help = "Management command to run reports for an election date"
    report_choices_str = ", ".join(["all"] + ALL_REPORT_CLASSES)

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
            help=f"The name of the report(s) to run, comma separated. Defaults to all. Choices: {self.report_choices_str}",
            required=False,
            default=None,
        )

        parser.add_argument(
            "--election-type",
            action="store",
            help="The election type to use when running reports",
            required=False,
        )

        parser.add_argument(
            "--register",
            action="store",
            help="The register to use when running reports",
            required=False,
        )

        parser.add_argument(
            "--england-only",
            action="store_true",
            help="Run reports for England only",
            required=False,
            default=False,
        )

    def handle(self, *args, **options):
        if options["reports"] is None:
            print("Pick one report or pass 'all'")
            print("\n".join([f"\t{name}" for name in ALL_REPORT_CLASSES]))
            return
        if options["reports"] == "all":
            reports = ALL_REPORT_CLASSES
        else:
            reports = options["reports"].split(",")

        for report in reports:
            report_runner(
                name=report,
                date=options["date"],
                election_type=options["election_type"],
                register=options["register"],
                england_only=options["england_only"],
            )
