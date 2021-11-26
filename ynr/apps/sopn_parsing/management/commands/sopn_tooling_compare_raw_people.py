import json
import os

from django.core.management import call_command
from django.core.management.base import BaseCommand

from candidates.models import Ballot
from bulk_adding.models import RawPeople


class Command(BaseCommand):
    def handle(self, *args, **options):
        """
        - Check we have a baseline file to compare with
        - Prepare some OfficialDocuments
        - Re-parse the documents
        - Loop through the created RawPeople objects, comparing to our baseline
        to make sure that we are parsing at least as many people as before
        - If no asserts failed, use the data to write a new baseline file
        """
        raw_people_file = "ynr/apps/sopn_parsing/tests/data/sopn_baseline.json"
        assert os.path.isfile(raw_people_file)

        call_command("sopn_tooling_create_official_documents")
        call_command("sopn_parsing_extract_page_numbers", "--reparse")
        call_command("sopn_parsing_extract_tables", "--reparse")
        call_command("sopn_parsing_parse_tables", "--reparse")

        with open(raw_people_file) as file:
            old_raw_people = json.loads(file.read())

        new_raw_people = {}
        for ballot in Ballot.objects.exclude(officialdocument__isnull=True):
            try:
                raw_people = ballot.rawpeople.data
            except RawPeople.DoesNotExist:
                raw_people = []

            assert len(raw_people) >= len(
                old_raw_people[ballot.ballot_paper_id]
            )
            new_raw_people[ballot.ballot_paper_id] = raw_people

        call_command("sopn_tooling_write_baseline", data=new_raw_people)
