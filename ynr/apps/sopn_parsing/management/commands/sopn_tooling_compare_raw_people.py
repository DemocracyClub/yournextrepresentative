import json
import os

from django.core.management import call_command
from django.core.management.base import BaseCommand

from bulk_adding.models import RawPeople
from candidates.models import Ballot


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

        call_command("sopn_parsing_extract_page_numbers", testing=True)
        call_command("sopn_parsing_extract_tables", testing=True)
        call_command("sopn_parsing_parse_tables", testing=True)

        with open(raw_people_file) as file:
            old_raw_people = json.loads(file.read())

        old_raw_people_count = len(
            {k: v for k, v in old_raw_people.items() if v}
        )
        self.stdout.write(f"Old raw people count: {old_raw_people_count}")

        new_raw_people = {}
        for ballot in Ballot.objects.exclude(officialdocument__isnull=True):

            try:
                raw_people = ballot.rawpeople.data
            except RawPeople.DoesNotExist:
                raw_people = []

            if ballot.ballot_paper_id not in old_raw_people:
                self.stdout.write(
                    "New ballot not previously parsed - adding data to new raw people but skipping comparisons"
                )
                new_raw_people[ballot.ballot_paper_id] = raw_people
                continue

            old_raw_people_for_ballot = old_raw_people[ballot.ballot_paper_id]
            old_count = len(old_raw_people_for_ballot)
            new_count = len(raw_people)
            assert new_count >= old_count

            for candidacy in old_raw_people_for_ballot:
                assert candidacy in raw_people

            new_raw_people[ballot.ballot_paper_id] = raw_people

        self.stdout.write(f"New raw people count: {RawPeople.objects.count()}")

        call_command("sopn_tooling_write_baseline", data=new_raw_people)
