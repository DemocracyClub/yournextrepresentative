# making a report of uncontested ballots, going back to 2016
# include all cancelled ballots for all reasons

from django.core.management import BaseCommand
from elections.models import Election


class Command(BaseCommand):
    def handle(self, *args, **options):
        self.find_uncontested_ballots()

    def find_uncontested_ballots(self):
        uncontested_ballots = []
        # created a qs of all ballots since 2016 where seats_contested ==  excluding cancelled ballots
        qs = Election.objects.filter(election_date__gte="2016-01-01").order_by(
            "election_date"
        )

        for election in qs:
            # find the related ballot
            for ballot in election.ballot_set.all():
                if ballot.uncontested is True:
                    uncontested_ballots.append(ballot)
        self.write_report(uncontested_ballots)
        print(
            f"Report written for {len(uncontested_ballots)} uncontested ballots"
        )
        return uncontested_ballots

    def write_report(self, uncontested_ballots):
        with open("uncontested_ballots.csv", "w") as report:
            report.write(
                "ballot_date,id,ballot_paper_id,cancelled,ballot.cancelled_status_text\n"
            )
            for ballot in uncontested_ballots:
                ballot_date = ballot.election.election_date.strftime("%d %b %Y")
                report.write(
                    f"{ballot_date},{ballot.id},{ballot.ballot_paper_id},{ballot.cancelled} {ballot.cancelled_status_text}  \n"
                )
            report.close()
