import json
import os

from candidates.models import Ballot
from bulk_adding.models import RawPeople
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    """This command uses the ballots endpoint to loop over each
    ballot and store each sopn pdf (uploaded_file) locally"""

    def add_arguments(self, parser):
        parser.add_argument(
            "--data",
            action="store",
            help="Dictionary of raw people to write as a baseline",
        )

    def handle(self, *args, **options):
        json_data = options["data"] or {}
        if not json_data:
            for ballot in Ballot.objects.exclude(officialdocument__isnull=True):
                raw_people = getattr(ballot, "rawpeople", [])
                try:
                    raw_people = ballot.rawpeople.data
                except RawPeople.DoesNotExist:
                    raw_people = []

                json_data[ballot.ballot_paper_id] = raw_people

        file_path = os.path.join(
            os.getcwd(), "ynr/apps/sopn_parsing/tests/data/sopn_baseline.json"
        )
        with open(file_path, "w") as f:
            f.write(json.dumps(json_data))
