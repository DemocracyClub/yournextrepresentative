from candidates.models import Ballot
from resultsbot.importers.base_historic_results_importer import (
    BaseImportHistoricResults,
)


class Command(BaseImportHistoricResults):
    help = """
    Import historic results data from the resultsbot csv file
    """
    url = "https://docs.google.com/spreadsheets/d/e/2PACX-1vTHlLmw-K_n7kifq0V9biNOefUXG6ejAeMXp1t04R7y-8OnOvhji32gFL5Viu7KLruoSCJkO_ApdJRH/pub?gid=827031370&single=true&output=csv"

    def parse_csv(self, csv_file):
        ballot_didnt_exist = []
        seen = set()
        records_to_save = []

        for row in csv_file:
            ballot_paper_id = row["ballot_paper_id"]
            if ballot_paper_id in seen:
                continue

            seen.add(ballot_paper_id)
            seats_contested = row["seats_contested"]

            try:
                ballot = Ballot.objects.get(ballot_paper_id=ballot_paper_id)
                if ballot.winner_count != int(seats_contested):
                    ballot.winner_count = seats_contested
                    records_to_save.append(ballot)
            except Ballot.DoesNotExist:
                ballot_didnt_exist.append(ballot_paper_id)
                continue

        print(
            f"Found {len(records_to_save)} ballots with mismatched winner counts."
        )
        for ballot in ballot_didnt_exist:
            print(
                f"Ballot paper ID {ballot} does not exist in the database. Please check manually"
            )
        return records_to_save
