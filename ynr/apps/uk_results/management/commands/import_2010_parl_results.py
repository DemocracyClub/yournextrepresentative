from django.core.management.base import BaseCommand
from django.contrib.postgres.search import SearchQuery, SearchVector
from slugify import slugify
from candidates.models.db import EditType, LoggedAction
from candidates.models.popolo_extra import Ballot
from django.db.models.functions import Length
from popolo.models import Membership
from resultsbot.helpers import ResultsBot

from uk_results.helpers import read_csv_from_url
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

    def find_candidacy(self, ballot, name):
        # exact search first
        try:
            return ballot.membership_set.get(person__name__iexact=name)
        except Membership.DoesNotExist:
            pass

        # fallback to a smarter searching
        vector = SearchVector("person__name", "person__other_names__name")
        candidates = ballot.membership_set.annotate(names=vector)
        try:
            return candidates.get(names=name)
        except (Membership.DoesNotExist, Membership.MultipleObjectsReturned):
            pass

        # get less specific - split the name and try and find a single match where at
        # least one of the names match
        query = " | ".join(name.split(" "))
        sq = SearchQuery(query, search_type="raw")
        try:
            return candidates.get(names=sq)
        except (Membership.DoesNotExist, Membership.MultipleObjectsReturned):
            # cant find this candidate
            url = f"http://candidates.democracyclub.org.uk{ballot.get_absolute_url()}"
            self.not_found.append(
                f"Cant find a membership for {name}. Check candidates at:\n{url}"
            )
            self.cant_find += 1
            return None

    def create_results(self, ballot, row):
        resultset, created = models.ResultSet.objects.update_or_create(
            ballot=ballot,
            defaults={
                "turnout_percentage": row["% Turnout"],
                "source": self.url,
            },
        )
        for candidate_data in self.current_candidates:
            resultset.candidate_results.update_or_create(
                membership=candidate_data.pop("membership"),
                defaults={**candidate_data},
            )

        _, changed = resultset.record_version()

        if changed:
            self.stdout.write("Recorded new results!")
            self.results_added += 1
            resultsbot = ResultsBot()
            resultsbot._mark_candidates_as_winner(resultset)

            LoggedAction.objects.create(
                user=resultset.user,
                action_type="entered-results-data",
                source=resultset.source,
                ballot=resultset.ballot,
                edit_type=EditType.BOT.name,
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
        self.current_ballot = Ballot(pk=None)
        self.current_candidates = []
        self.results_added = 0
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
            candidate_data = {
                "membership": candidate,
                "num_ballots": num_ballots,
                "is_winner": row["Elected"] == "*",
            }
            # are we still on same ballot?
            if self.current_ballot.pk == ballot.pk:
                # yes - so add the candidate to our list
                self.current_candidates.append(candidate_data)
            else:
                # no - so create a new candidate list
                self.current_candidates = [candidate_data]

            # if matched candidates is equal to memberships on the ballot we can
            # create the results
            if len(self.current_candidates) == ballot.membership_set.count():
                self.create_results(ballot=ballot, row=row)

            self.current_ballot = ballot

        self.stdout.write(f"Created {self.results_added} new results")
        self.stdout.write(f"{self.cant_find} candidates couldnt be found:")
        self.stdout.write("\n".join(self.not_found))
