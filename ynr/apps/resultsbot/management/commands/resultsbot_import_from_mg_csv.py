import csv
import os

from django.core.management.base import BaseCommand

import resultsbot
from elections.models import Election
from resultsbot.helpers import ResultsBot
from resultsbot.importers.modgov import ModGovImporter


class Command(BaseCommand):
    def handle(self, **options):
        id_to_url = {}

        path = os.path.join(
            os.path.dirname(resultsbot.__file__), "election_id_to_url.csv"
        )
        with open(path) as f:
            csv_file = csv.reader(f)
            for line in csv_file:
                if not line:
                    continue
                id_to_url[line[0]] = line[1]

        all_candidates = []

        for election_id, url in id_to_url.items():
            election = Election.objects.get(slug=election_id)
            if not election.current:
                continue
            print(election_id, url)
            importer = ModGovImporter(election_id, url=url)
            ballot_with_result = [
                hasattr(ballot, "resultset")
                for ballot in importer.election.ballot_set.all()
            ]
            if all(ballot_with_result):
                continue
            importer.get_data()
            for div in importer.divisions():
                if (
                    div.local_area.ballot_paper_id
                    == "local.tower-hamlets.whitechapel.2018-05-03"
                ):
                    continue
                if (
                    div.local_area.ballot_paper_id
                    == "local.eastleigh.eastleigh-north.2018-05-03"
                ):
                    continue

                if hasattr(div.local_area, "resultset"):
                    continue

                candidates = list(importer.candidates(div))
                candidates_len = len(candidates)
                if candidates_len != div.local_area.membership_set.count():
                    print(
                        f"Only found {candidates_len} candidates for {div.local_area.ballot_paper_id}, skipping"
                    )
                    continue

                # avoids storing a partial result
                has_all_votes = all([c.votes for c in candidates])
                if not has_all_votes:
                    print(
                        f"Couldn't find a vote count for every candidate, skipping {div.local_area.ballot_paper_id}"
                    )
                    continue

                all_candidates += candidates
                print("Adding results for {}".format(div.title))
                bot = ResultsBot()
                bot.add_results(
                    division=div,
                    candidate_list=candidates,
                    source=importer.api_url_to_web_url(url),
                )
        print(len(all_candidates))
