from pathlib import Path

from django.core.management import BaseCommand

from django.conf import settings

from cached_counts.models import CachedReport
from cached_counts.report_helpers import (
    ALL_REPORT_CLASSES,
    report_runner,
    BaseReport,
)


class Command(BaseCommand):
    help = "Create JSON versions of reports for all elections in settings.REPORT_DATES"

    def handle(self, *args, **options):
        reports_dir = Path.cwd() / "ynr/apps/cached_counts/reports/"
        reports_dir.mkdir(exist_ok=True)

        for group_id, report_data in settings.REPORT_DATES.items():
            election_type, report_date = group_id.split(".")
            registers = report_data.get("registers", ["GB"])
            for report_class in ALL_REPORT_CLASSES:
                for register in registers:
                    report: BaseReport = report_runner(
                        name=report_class,
                        date=report_date,
                        election_type=election_type,
                        register=register,
                    )
                    CachedReport.objects.update_or_create(
                        election_date=report_date,
                        group_id=group_id,
                        report_name=report_class,
                        register=register,
                        report_json=report.as_dict(),
                    )
                    # print(report.name)
                    # print(report.as_text())
                    # print()
                    # print()
                    # print()
                    # print(report.as_dict())
