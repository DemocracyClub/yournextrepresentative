from collections import defaultdict
from candidates.models.popolo_extra import Ballot

from uk_results.helpers import read_csv_from_url
from uk_results.management.commands.import_2010_parl_results import (
    Command as ResultsImporterCommand,
)


class Command(ResultsImporterCommand):
    """
    Imports results for the 2015 general election. The data was taken from the
    House of Commons website, and then published in the Democracy Club google
    drive to make it easier to import.
    Many of the methods used to create objects are inherited from the management
    command in import_2010_parl_results.
    """

    url = "https://docs.google.com/spreadsheets/d/e/2PACX-1vTh6_PoqDSn-s7N8Tnd6JrQ9JBcGeHv1ULlLngJ6Zmw3YFAKYVmp8Vesge7SXzPTGnt80rzyPId5u_Y/pub?gid=0&single=true&output=csv"
    election_date = "2017-06-08"

    def handle(self, **options):
        self.qs = Ballot.objects.exclude(
            ballot_paper_id__contains=".by."
        ).filter(election__election_date=self.election_date, cancelled=False)

        self.cant_find = 0
        self.not_found = []
        self.results_added = 0

        ballot_data = defaultdict(list)
        self.turnouts = {}
        self.stdout.write("Getting the data...")
        for row in read_csv_from_url(url=self.url):
            seat = row["constituency_name"].lower().strip()

            if seat in self.EDGECASES:
                seat = self.EDGECASES[seat]

            ballot = self.find_ballot(seat=seat)

            first_name = row["firstname"].strip()
            last_names = row["surname"].strip()
            candidate_name = f"{first_name} {last_names}"
            candidate = self.find_candidacy(
                ballot=ballot, name=candidate_name, party=row["party_name"]
            )

            if not candidate:
                self.stderr.write(f"Couldnt find {candidate_name}")
                continue

            num_ballots = int(row["votes"])
            candidate_dict = {
                "membership": candidate,
                "num_ballots": num_ballots,
            }
            ballot_data[ballot].append(candidate_dict)

        self.stdout.write("Creating results...")
        for ballot, candidates in ballot_data.items():
            self.create_results(ballot, candidates)

        self.stdout.write(f"Created {self.results_added} new results")
        self.stdout.write(f"{self.cant_find} candidates couldnt be found:")
        self.stdout.write("\n".join(self.not_found))
