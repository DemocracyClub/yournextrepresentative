import csv
import os

import resultsbot
from django.core.management.base import BaseCommand
from resultsbot.importers.modgov import ModGovElectionMatcher
from uk_results.helpers import read_csv_from_url


class Command(BaseCommand):
    # def add_arguments(self, parser):
    #     parser.add_argument(
    #         '--url',
    #         action='store',
    #         required=True
    #     )
    #     parser.add_argument(
    #         '--election_id',
    #         action='store',
    #         required=True
    #     )

    def handle(self, **options):
        id_to_url = {}
        path = os.path.join(
            os.path.dirname(resultsbot.__file__), "election_id_to_url.csv"
        )

        with open(path) as f:
            csv_file = csv.reader(f)
            for line in csv_file:
                try:
                    id_to_url[line[0]] = line[1]
                except IndexError:
                    continue

        found_elections = self.get_found_elections(path)

        url = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQJT-XOl2ryx0crgPLj5phgeLmJ2C_jRxVJ0WQdiGNUjguQ4xgTIe_cNTNc7VIELt4XaRy6RyCJSoAo/pub?output=csv"
        data = []
        for row in read_csv_from_url(url):
            # uses_mg = row.get("Uses MG?") or ""
            # if uses_mg.strip().upper() != "Y":
            #     continue

            election_id = row["Election ID"]
            url = row["ModGov Install"]
            print(repr(election_id))
            if not election_id or election_id in found_elections:
                continue

            data.append((election_id, url))
        for election_id, url in data:
            if election_id in id_to_url:
                continue
            print(election_id)
            matcher = ModGovElectionMatcher(
                base_domain=url, election_id=election_id
            )
            try:
                matcher.find_elections()
                election = matcher.match_to_election()
            except KeyboardInterrupt:
                raise
            except Exception as e:
                print("Error on {} ({})".format(election_id, e))
                continue
            if election:
                # print("This is the URL for the given election")
                print("{},{}".format(election_id, election.url))
                with open(path, "a") as f:
                    f.write("\n{},{}".format(election_id, election.url))

            else:
                print("No URL found for {}!".format(election_id))
                print("\tHighest ID was {}".format(matcher.lookahead))
                print("\tTry the following for debugging:")
                print("\t" + matcher.format_elections_html_url())
                print("\t" + matcher.format_elections_api_url())

    def get_found_elections(self, path):
        found_elections = []
        self.stdout.write(f"Reading found elections from {path}")
        try:
            with open(path) as f:
                csv_file = csv.reader(f)
                for line in csv_file:
                    found_elections.append(line[0])

        except FileNotFoundError:
            return []
        return found_elections
