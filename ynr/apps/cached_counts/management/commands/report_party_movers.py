from collections import defaultdict

from django.core.management import BaseCommand
from django.db.models import Count, Prefetch
from people.models import Person
from popolo.models import Membership

YEARS = [
    2016,
    2017,
    2018,
    2019,
    2020,
    2021,
    2022,
]


class Command(BaseCommand):
    def handle(self, *args, **options):
        qs = (
            Person.objects.filter(
                memberships__ballot__ballot_paper_id__startswith="local."
            )
            .annotate(party_count=Count("memberships__party", distinct=True))
            .filter(party_count__gt=1)
            .prefetch_related(
                Prefetch(
                    "memberships",
                    Membership.objects.order_by(
                        "ballot__election__election_date"
                    ).filter(ballot__ballot_paper_id__startswith="local."),
                ),
                "memberships__party",
                "memberships__ballot",
            )
        )

        def year_of_membership(membership: Membership) -> int:
            return int(membership.ballot.election.election_date.year)

        def get_party_name_for_year(
            memberships: Membership.objects.all, year: int
        ) -> str:
            first_membership: Membership = memberships.first()
            if year_of_membership(first_membership) >= year:
                return first_membership.party_name
            for membership in sorted(
                memberships.all(), key=lambda mem: year_of_membership(mem)
            ):
                mem_year = year_of_membership(membership)
                if mem_year == year:
                    return membership.party_name
            return memberships.last().party_name

        # print(get_party_name_for_year(Person.objects.get(pk=25544).memberships.order_by("").all(),
        #                         2016))
        # import sys
        # sys.exit()

        # party_count_by_year = {year: defaultdict(int) for year in YEARS}
        all_party_years = []

        for person in qs:
            person_parties_by_year = {}
            for year in YEARS:
                person_parties_by_year[year] = get_party_name_for_year(
                    person.memberships.all(), year
                )
            # if not len(set(person_parties_by_year.values())) > 1:
            #     continue
            if "UK Independence Party (UKIP)" not in str(
                person_parties_by_year.values()
            ):
                continue
            all_party_years.append(person_parties_by_year)

        year_change_count_for_party = {}
        for year in YEARS[:-1]:
            move_data = {
                "step_from": year,
                "step_to": year + 1,
                "parties": defaultdict(lambda: defaultdict(int)),
            }
            # parties_this_year = sorted(party_count_by_year[year])
            # parties_next_year = sorted(party_count_by_year[year+1])
            for person_row in all_party_years:
                move_data["parties"][person_row[year]][
                    person_row[year + 1]
                ] += 1
            year_change_count_for_party[year] = move_data

        for year, move_data in year_change_count_for_party.items():
            for party_from, party_to_dict in move_data["parties"].items():
                for party_to, count in party_to_dict.items():
                    row = [
                        party_from,
                        party_to,
                        str(count),
                        str(move_data["step_from"]),
                        str(move_data["step_to"]),
                    ]
                    print("\t".join(row))
