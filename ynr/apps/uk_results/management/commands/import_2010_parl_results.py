from collections import defaultdict
from django.core.management.base import BaseCommand
from django.contrib.postgres.search import SearchQuery
from candidates.models.popolo_extra import Ballot
from django.db.models.functions import Length
from popolo.models import Membership
from resultsbot.helpers import ResultsBot
from uk_results.helpers import RecordBallotResultsHelper, read_csv_from_url
from uk_results import models


class Command(BaseCommand):

    EDGECASES = {
        "ynys mon": "ynys môn",
        "down south": "south down",
        "down north": "north down",
    }

    def find_ballot(self, seat):
        try:
            return self.qs.get(post__label__iexact=seat)
        except Ballot.DoesNotExist:
            pass

        matches = self.qs.filter(post__label__search=seat)
        try:
            return matches.get()
        except Ballot.MultipleObjectsReturned:
            return matches.annotate(label_len=Length("post__label")).get(
                label_len=len(seat)
            )

    def find_candidacy(self, ballot, name, party=None):
        # exact search first
        try:
            return ballot.membership_set.get(person__name__iexact=name)
        except Membership.DoesNotExist:
            pass

        # fallback to a searcing on search vector field
        sq = SearchQuery(name, config="english")
        try:
            return ballot.membership_set.get(person__name_search_vector=sq)
        except (Membership.DoesNotExist, Membership.MultipleObjectsReturned):
            pass

        # get less specific - split the name and try and find a single match where at
        # least one of the names match
        query = " | ".join(name.split(" "))
        sq = SearchQuery(query, search_type="raw", config="english")
        try:
            return ballot.membership_set.get(person__name_search_vector=sq)
        except (Membership.DoesNotExist, Membership.MultipleObjectsReturned):
            pass

        if party:
            try:
                candidate = ballot.membership_set.get(
                    party__name__icontains=party
                )
                self.stdout.write(
                    "Found candidate by their party. Double check?"
                )
                self.stdout.write(
                    f"Name: {name}\nParty: {party}\nBallot: {ballot.get_absolute_url()}"
                )
                return candidate
            except (
                Membership.DoesNotExist,
                Membership.MultipleObjectsReturned,
            ):
                pass
        # cant find this candidate
        url = (
            f"http://candidates.democracyclub.org.uk{ballot.get_absolute_url()}"
        )
        self.not_found.append(
            f"Cant find a membership for {name}. Check candidates at:\n{url}"
        )
        self.cant_find += 1
        return None

    def create_results(self, ballot, candidates):

        if ballot.membership_set.count() != len(candidates):
            return self.stdout.write(
                "Incorrect number of candidates for ballot, skipping"
            )

        defaults = {"source": self.url}
        if self.turnouts:
            defaults["turnout_percentage"] = self.turnouts[
                ballot.ballot_paper_id
            ]

        resultset, created = models.ResultSet.objects.update_or_create(
            ballot=ballot, defaults=defaults
        )
        for candidate_dict in candidates:
            resultset.candidate_results.update_or_create(
                membership=candidate_dict.pop("membership"),
                defaults={**candidate_dict},
            )

        _, changed = resultset.record_version()

        if changed:
            self.stdout.write("Recorded new results!")
            self.results_added += 1
            winner = (
                resultset.candidate_results.order_by("-num_ballots")
                .first()
                .membership.person
            )
            resultsrecorder = RecordBallotResultsHelper(
                ballot=ballot, user=ResultsBot().user
            )
            resultsrecorder.mark_person_as_elected(
                person=winner, source=resultset.source
            )

        created_or_updated = "Created" if created else "Updated"
        self.stdout.write(f"{created_or_updated} a result")

    def handle(self, **options):
        self.url = "https://docs.google.com/spreadsheets/d/e/2PACX-1vSpxOSrWevLyMIugBuszezmeuhdQc_ktkObCJ4BsrOlcJfZgS6iMWWzIZ4Y8jTUTguIh3lUMhZmYqxc/pub?gid=1&single=true&output=csv"

        self.qs = Ballot.objects.exclude(
            ballot_paper_id__contains=".by."
        ).filter(election__election_date="2010-05-06", cancelled=False)

        self.cant_find = 0
        self.not_found = []
        self.results_added = 0

        ballot_data = defaultdict(list)
        self.turnouts = {}
        self.stdout.write("Getting the data...")
        for row in read_csv_from_url(url=self.url):
            seat = row["Seat"].lower().strip()

            if seat in self.EDGECASES:
                seat = self.EDGECASES[seat]

            ballot = self.find_ballot(seat=seat)

            candidate_name = " ".join(
                reversed(row["Candidate"].split(", "))
            ).strip()
            candidate = self.find_candidacy(ballot=ballot, name=candidate_name)

            if not candidate:
                continue

            num_ballots = int(row["Vote"].replace(",", ""))
            candidate_dict = {
                "membership": candidate,
                "num_ballots": num_ballots,
            }
            ballot_data[ballot].append(candidate_dict)
            self.turnouts[ballot.ballot_paper_id] = row["% Turnout"]

        self.stdout.write("Creating results...")
        for ballot, candidates in ballot_data.items():
            self.create_results(ballot, candidates)

        self.stdout.write(f"Created {self.results_added} new results")
        self.stdout.write(f"{self.cant_find} candidates couldnt be found:")
        self.stdout.write("\n".join(self.not_found))
