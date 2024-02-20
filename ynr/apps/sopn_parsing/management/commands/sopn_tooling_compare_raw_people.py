import json
import os
from collections import Counter

from bulk_adding.models import RawPeople
from candidates.models import Ballot
from django.core.management import call_command
from official_documents.models import OfficialDocument
from popolo.models import Membership
from sopn_parsing.helpers.command_helpers import BaseSOPNParsingCommand
from sopn_parsing.models import CamelotParsedSOPN


class Command(BaseSOPNParsingCommand):
    CORRECT_EXACTLY = "correct_exactly"
    NUM_CORRECT_MISSING_PARTIES = "num_correct_some_parties_missing"
    NUM_INCORRECT = "num_incorrect"
    ZERO_CANDIDATES = "zero_candidates"

    def add_arguments(self, parser):
        super().add_arguments(parser)
        parser.add_argument("--loud", action="store_true", default=False)

    def handle(self, *args, **options):
        """
        - Check we have a baseline file to compare with
        - Prepare some OfficialDocuments
        - Re-parse the documents
        - Loop through the created RawPeople objects, comparing to our baseline
        to make sure that we are parsing at least as many people as before
        - If no asserts failed, use the data to write a new baseline file
        """

        self.loud = options.pop("loud")

        self.candidates_results = {
            "correct_exactly": [],
            "num_correct_some_parties_missing": [],
            "num_incorrect": [],
            "zero_candidates": [],
        }

        raw_people_file = "ynr/apps/sopn_parsing/tests/data/sopn_baseline.json"
        if not os.path.isfile(raw_people_file):
            call_command("sopn_tooling_write_baseline")
            self.stdout.write("Baseline file didn't exist so one was created")

        options.update({"testing": True})

        OfficialDocument.objects.update(relevant_pages="")
        call_command("sopn_parsing_extract_page_numbers", *args, **options)
        CamelotParsedSOPN.objects.all().delete()
        call_command("sopn_parsing_extract_tables", *args, **options)
        RawPeople.objects.all().delete()
        call_command("sopn_parsing_parse_tables", *args, **options)

        with open(raw_people_file) as file:
            old_raw_people = json.loads(file.read())

        self.new_raw_people = {}
        for ballot in Ballot.objects.exclude(officialdocument__isnull=True):
            ballot_data = old_raw_people.get(ballot.ballot_paper_id, {})

            self.compare_relevant_pages(ballot=ballot, ballot_data=ballot_data)

            self.compare_raw_people(ballot=ballot, ballot_data=ballot_data)

        # display some overall totals
        self.stdout.write(
            "Old total 'people' parsed WAS {old}\n"
            "New total 'people' parsed IS {new}".format(
                old=self.count_people_parsed(old_raw_people),
                new=self.count_people_parsed(self.new_raw_people),
            )
        )

        old_raw_people_obj_count = len(
            {k: v for k, v in old_raw_people.items() if v["raw_people"]}
        )
        new_raw_people_obj_count = RawPeople.objects.count()
        style = self.style.SUCCESS
        if new_raw_people_obj_count < old_raw_people_obj_count:
            style = self.style.ERROR
        self.stdout.write(
            style(
                f"Old RawPeople count: {old_raw_people_obj_count}\n"
                f"New total RawPeople count: {new_raw_people_obj_count}"
            )
        )

        for result, ballots in self.candidates_results.items():
            total = len(ballots)
            self.stdout.write(f"{total} ballots parsed {result}")
            # Write a new baseline
        call_command("sopn_tooling_write_baseline")

    def compare_relevant_pages(self, ballot, ballot_data):
        old_relevant_pages = ballot_data.get("relevant_pages", "")
        new_relevant_pages = ballot.sopn.relevant_pages

        if old_relevant_pages != new_relevant_pages:
            self.stdout.write(
                self.style.WARNING(
                    f"RELEVANT PAGES CHANGED FROM {old_relevant_pages} to {new_relevant_pages} for {ballot.ballot_paper_id}"
                )
            )

    def compare_raw_people(self, ballot, ballot_data):
        try:
            raw_people = ballot.rawpeople.data
        except RawPeople.DoesNotExist:
            raw_people = []

        old_raw_people_for_ballot = ballot_data.get("raw_people", [])
        old_count = len(old_raw_people_for_ballot)
        new_count = len(raw_people)
        if new_count < old_count:
            self.stderr.write(
                f"Uh oh, parsed people for {ballot.ballot_paper_id} decreased from {old_count} to {new_count}. Stopping."
            )

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
                    f"Parsed data changed for {ballot.ballot_paper_id}\n"
                    f"New raw people data:\n"
                    f"{raw_people}\n"
                    "Missing people:"
                )
            )
            for person in changed_people:
                self.stderr.write(str(person))

        self.new_raw_people[ballot.ballot_paper_id] = {"raw_people": raw_people}

        self.parties_correct(ballot, raw_people)

    def count_people_parsed(self, raw_people_data):
        """
        Returns the total number of "people" that were parsed.
        NB that just because something was parsed, it doesnt mean that it was
        accurately parsed. Therefore this total is best used to look for large
        changes that should then be checked in detail.
        """
        return sum(
            [len(data["raw_people"]) for data in raw_people_data.values()]
        )

    def parties_correct(self, ballot, raw_people_for_ballot):
        candidates = Membership.objects.filter(ballot=ballot)
        if not candidates:
            self.stdout.write(
                self.style.WARNING(
                    f"We dont have candidates for {ballot.ballot_paper_id}. Try updating with the live site first?"
                )
            )

        if not raw_people_for_ballot:
            self.candidates_results[self.ZERO_CANDIDATES].append(
                ballot.ballot_paper_id
            )
            return None

        num_candidates_correct = candidates.count() == len(
            raw_people_for_ballot
        )

        if self.loud:
            if num_candidates_correct:
                self.stdout.write(
                    self.style.SUCCESS(
                        f"Correct number of people parsed as expected for {ballot.ballot_paper_id}"
                    )
                )
            else:
                self.stdout.write(
                    self.style.ERROR(
                        f"Incorrect number of people parsed for {ballot.ballot_paper_id}"
                    )
                )

        parsed = sorted(
            [person["party_id"] for person in raw_people_for_ballot]
        )
        expected = list(
            candidates.values_list("party__ec_id", flat=True).order_by(
                "party__ec_id"
            )
        )

        if parsed == expected:
            return self.candidates_results[self.CORRECT_EXACTLY].append(
                ballot.ballot_paper_id
            )

        # count number of each missing party ID as there could be more than one
        # missing candidate for a party e.g. 1 missing Green, 2 missing independents
        parsed = Counter(parsed)
        expected = Counter(expected)
        missing = expected - parsed
        if missing:
            total = sum(missing.values())
            self.stderr.write(
                f"{total} MISSING parties for {ballot.ballot_paper_id} (party_id:num_missing)\n{missing}"
            )
        else:
            # sometimes we incorrectly parse extra people - often independents
            # due to an empty row
            extras = parsed - expected
            total = sum(extras.values())
            self.stderr.write(
                f"{total} EXTRA parties for {ballot.ballot_paper_id}\n{extras}"
            )

        if num_candidates_correct:
            return self.candidates_results[
                self.NUM_CORRECT_MISSING_PARTIES
            ].append(ballot.ballot_paper_id)

        return self.candidates_results[self.NUM_INCORRECT].append(
            ballot.ballot_paper_id
        )
