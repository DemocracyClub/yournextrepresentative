import contextlib
import csv
from typing import Dict, List

from candidatebot.helpers import CandidateBot
from django.core.management.base import BaseCommand
from django.db import IntegrityError
from people.models import Person


class Command(BaseCommand):
    help = """
    Expects a CSV in the format that the CSV builder exports. 
    
    That is, the CSV has to support the same column headings that the CSV exporter
    does. 
    
    CandidateBot doesn't support all fields that the exporter does, including candidacies, photos, results, etc.
    
    It does support person identifier fields.
    
    Non-supported fields will be ignored.
    """

    def add_arguments(self, parser):
        parser.add_argument(
            "filename", help="Path to the file with the email addresses"
        )
        parser.add_argument(
            "--source",
            help="Source of the data. The source CSV column takes precedence",
        )
        parser.add_argument(
            "--replace",
            help="""If a field already exists on a candidate, use this to replace that value. 
            Otherwise the field is skipped.""",
            action="store_true",
        )

    def handle(self, **options):
        with open(options["filename"], "r") as fh:
            reader: List[Dict] = csv.DictReader(fh)
            for row in reader:
                source = row.get("source", options.get("source"))
                person_id = row["person_id"]
                if not person_id:
                    continue
                if not source:
                    raise ValueError("A source is required")

                try:
                    bot = CandidateBot(
                        person_id, update=options.get("replace", False)
                    )
                    self.import_fields_for_person(bot, row)
                except Person.DoesNotExist:
                    self.stdout.write(
                        "Person ID {} not found".format(person_id)
                    )
                bot.save(source)

    def import_fields_for_person(self, bot, row):
        for field_name in bot.SUPPORTED_EDIT_FIELDS:
            if not row.get(field_name):
                continue
            with contextlib.suppress(ValueError):
                try:
                    bot.edit_field(field_name, row.get(field_name))
                except IntegrityError:
                    self.stderr.write(
                        f"{field_name} for {row['person_id']} not updated. Use --replace to overwrite"
                    )
