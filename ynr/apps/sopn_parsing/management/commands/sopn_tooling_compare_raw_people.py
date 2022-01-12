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
        if not os.path.isfile(raw_people_file):
            # only write a file if we dont already have one otherwise a failing
            # run (e.g. people went down) would overwrite our last baseline file
            call_command("sopn_tooling_write_baseline")
            self.stdout.write("Baseline file didn't exist so one was created")

        call_command("sopn_parsing_extract_page_numbers", testing=True)
        call_command("sopn_parsing_extract_tables", testing=True)
        call_command("sopn_parsing_parse_tables", testing=True)

        with open(raw_people_file) as file:
            old_raw_people = json.loads(file.read())

        old_raw_people_count = len(
            {k: v for k, v in old_raw_people.items() if v}
        )
        self.stdout.write(f"Old RawPeople count: {old_raw_people_count}")

        new_raw_people = {}
        for ballot in Ballot.objects.exclude(officialdocument__isnull=True):

            try:
                raw_people = ballot.rawpeople.data
            except RawPeople.DoesNotExist:
                raw_people = []

            old_raw_people_for_ballot = old_raw_people[ballot.ballot_paper_id]
            old_count = len(old_raw_people_for_ballot)
            new_count = len(raw_people)
            if new_count < old_count:
                self.stderr.write(
                    f"Uh oh, parsed people for {ballot.ballot_paper_id} decreased from {old_count} to {new_count}. Stopping."
                )
                raise Exception("Raw people went down")

            if new_count > old_count:
                self.stdout.write(
                    f"{ballot.ballot_paper_id} increased from {old_count} to {new_count} parsed people.\n"
                    f"Check the SOPN at https://candidates.democracyclub.org.uk{ballot.get_sopn_url()}."
                )
                for person in raw_people:
                    if person not in old_raw_people_for_ballot:
                        self.stdout.write(self.style.SUCCESS(person))

            # when people parsed have changed e.g. different name/different party print it for further checking
            changed_people = [
                person
                for person in old_raw_people_for_ballot
                if person not in raw_people
            ]
            if changed_people:
                self.stdout.write(
                    self.style.WARNING(
                        f"Number of people parsed for {ballot.ballot_paper_id} has not gone down but people have changed or are missing.\n"
                        f"New raw people data:\n"
                        f"{raw_people}\n"
                        "Missing people:"
                    )
                )
                for person in changed_people:
                    self.stderr.write(str(person))

            new_raw_people[ballot.ballot_paper_id] = raw_people

        # exit if this went down
        new_total = RawPeople.objects.count()
        assert (
            new_total >= old_raw_people_count
        ), "Total number of RawPeople objects created went down"

        self.stdout.write(
            self.style.SUCCESS(f"New total RawPeople count: {new_total}")
        )
        # Write a new baseline
        call_command("sopn_tooling_write_baseline", data=new_raw_people)
