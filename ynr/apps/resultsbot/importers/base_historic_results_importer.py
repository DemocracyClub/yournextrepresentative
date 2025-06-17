import abc
import csv

import requests
from django.conf import settings
from django.contrib.auth.models import User
from django.core.management import BaseCommand
from django.db import transaction


class BaseImportHistoricResults(BaseCommand, metaclass=abc.ABCMeta):
    help = """
    Base command to import historic results data set helpfully collated by Jason Leman.
    """
    source = "LEAP data at https://www.andrewteale.me.uk/leap/downloads"
    user = User.objects.get(username=settings.RESULTS_BOT_USERNAME)

    def add_arguments(self, parser):
        parser.add_argument(
            "-ff",
            "--from-file",
            help="To import from a file, pass in the path to the file",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Run the command without making any changes to the database",
        )

    def import_csv_from_url(self):
        url = self.url
        with requests.get(url, stream=True) as r:
            r.encoding = "utf-8"
            yield from csv.DictReader(r.iter_lines(decode_unicode=True))

    def import_csv_from_file(self, file_path):
        with open(file_path, "r", encoding="utf-8") as f:
            yield from csv.DictReader(f)

    @abc.abstractmethod
    def parse_csv(self, csv):
        pass

    def create_meta_events(self, record):
        """
        optional method to create meta events like ResultEvents or LoggedActions
        """
        pass

    @transaction.atomic
    def save_records(self, records):
        for record in records:
            record.save()
            self.create_meta_events(record)

    def handle(self, *args, **options):
        # Import the CSV file
        if options["from_file"]:
            csv_file = self.import_csv_from_file(options["from_file"])
        else:
            csv_file = self.import_csv_from_url()
        # Parse the CSV file
        records_to_save = self.parse_csv(csv_file)
        # Save the records
        if options["dry_run"]:
            self.stdout.write(
                f"Dry run: {len(records_to_save)} records would be updated."
            )
        else:
            self.save_records(records_to_save)
            self.stdout.write(
                f"Saved {len(records_to_save)} records to the database."
            )
