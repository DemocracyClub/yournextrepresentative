import json
import os

from django.db.models import Q

from candidates.models import Ballot
from bulk_adding.models import RawPeople
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    """
    Creates a JSON file to represent ballots that have an Officialdocument.
    Only include ballots where:
    - The source of the RawPeople is from parsing a PDF
    - No RawPeople were created from the OfficialDocument. This is so that we
    will know if we make make improvements that mean more RawPeople are parsed
    from an OfficialDocument
    """

    def add_arguments(self, parser):
        parser.add_argument(
            "--data",
            action="store",
            help="Dictionary of raw people to write as a baseline",
        )

    def handle(self, *args, **options):
        json_data = options["data"] or {}

        if not json_data:
            qs = Ballot.objects.exclude(officialdocument__isnull=True).filter(
                Q(rawpeople__source_type=RawPeople.SOURCE_PARSED_PDF)
                | Q(rawpeople__isnull=True)
            )
            for ballot in qs:
                raw_people = getattr(ballot, "rawpeople", [])
                try:
                    raw_people = ballot.rawpeople.data
                except RawPeople.DoesNotExist:
                    raw_people = []

                json_data[ballot.ballot_paper_id] = {
                    "raw_people": raw_people,
                    "relevant_pages": ballot.sopn.relevant_pages,
                }

        file_path = os.path.join(
            os.getcwd(), "ynr/apps/sopn_parsing/tests/data/sopn_baseline.json"
        )
        with open(file_path, "w") as f:
            f.write(json.dumps(json_data))
