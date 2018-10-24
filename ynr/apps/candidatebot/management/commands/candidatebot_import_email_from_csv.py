import csv

from django.core.management.base import BaseCommand

from candidatebot.helpers import CandidateBot
from people.models import Person


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument(
            "filename", help="Path to the file with the email addresses"
        )
        parser.add_argument(
            "--source",
            help="Source of the data. The source CSV column takes precedence",
        )

    def handle(self, **options):
        with open(options["filename"], "r") as fh:
            reader = csv.DictReader(fh)
            for row in reader:
                source = row.get("source", options.get("source"))
                if not row["democlub_id"]:
                    continue
                if not source:
                    raise ValueError("A source is required")

                try:
                    bot = CandidateBot(row["democlub_id"])
                    try:
                        bot.add_email(row["email"])
                        bot.save(source)
                    except ValueError:
                        # Email exists, move on
                        pass
                except Person.DoesNotExist:
                    print("Person ID {} not found".format(row["democlub_id"]))
                # print(row)
