"""
Highest number of candidates per seats & longest ballots (most parties contesting a seat?)
Geography – where are parties standing lots/no candidates - where are independents strongest, etc
Maybe strongest region groups (e.g. are Bath independents standing everywhere in bath?)
Gender
New parties
"""
import collections
import sys
from collections import Counter

from django.db.models import (
    Count,
    ExpressionWrapper,
    F,
    FloatField,
    Func,
    Sum,
    Prefetch,
)
from django.db.models.query_utils import Q

from candidates.models import Ballot
from django.conf import settings
from elections.filters import region_choices
from parties.models import Party
from people.models import Person
from popolo.models import Membership


EXCLUSION_IDS = [
    "local.flintshire.gwernymynydd.by.2021-05-06",
    "local.newport.victoria.by.2021-05-06",
    "local.bridgend.nant-y-moel.by.2021-05-06",
    "local.isle-of-anglesey.caergybi.by.2021-05-06",
    "local.isle-of-anglesey.seiriol.by.2021-05-06",
    "local.neath-port-talbot.aberavon.by.2021-05-06",
    "local.rhondda-cynon-taff.llantwit-fardre.by.2021-05-06",
    "local.rhondda-cynon-taff.penrhiwceiber.by.2021-05-06",
    "local.swansea.castle.by.2021-05-06",
    "local.swansea.llansamlet.by.2021-05-06",
    "local.stirling.forth-and-endrick.by.2021-05-06",
]


class BaseReport:
    def __init__(
        self,
        date,
        election_type=None,
        register=None,
        nation=None,
        elected=False,
        exclude_cancelled=False,
        nuts_code=None,
    ):
        self.date = date
        self.nation = nation
        self.election_type = election_type or "local"
        register = register or "GB"
        self.elected = elected
        self.exclude_cancelled = exclude_cancelled
        self.nuts_code = nuts_code

        self.ballot_qs = Ballot.objects.filter(
            election__election_date=self.date
        )
        if self.election_type != "all":
            self.ballot_qs = self.ballot_qs.filter(
                ballot_paper_id__startswith=self.election_type
            )
        self.ballot_qs = (
            self.ballot_qs.exclude(ballot_paper_id__in=EXCLUSION_IDS)
            .filter(post__party_set__slug=register.lower())
            .exclude(membership=None)
        )

        self.membership_qs = Membership.objects.filter(
            ballot__election__election_date=self.date
        )
        if self.election_type != "all":
            self.membership_qs = self.membership_qs.filter(
                ballot__ballot_paper_id__startswith=self.election_type
            )
        self.membership_qs = self.membership_qs.filter(
            ballot__post__party_set__slug=register.lower()
        ).exclude(ballot__ballot_paper_id__in=EXCLUSION_IDS)

        if self.nation:
            self.ballot_qs = self.ballot_qs.filter(
                tags__NUTS1__key__in=settings.NUTS_TO_NATION[self.nation]
            )
            self.membership_qs = self.membership_qs.filter(
                ballot__tags__NUTS1__key__in=settings.NUTS_TO_NATION[
                    self.nation
                ]
            )

        if self.nuts_code:
            self.ballot_qs = self.ballot_qs.filter(
                tags__NUTS1__key=self.nuts_code
            )
            self.membership_qs = self.membership_qs.filter(
                ballot__tags__NUTS1__key=self.nuts_code
            )

        if self.elected:
            self.membership_qs = self.membership_qs.filter(elected=True)

        if self.exclude_cancelled:
            self.ballot_qs = self.ballot_qs.exclude(cancelled=True)
            self.membership_qs = self.membership_qs.exclude(
                ballot__cancelled=True
            )

        template = "%(function)s(%(expressions)s AS FLOAT)"
        self.f_candidates = Func(
            F("candidates"), function="CAST", template=template
        )
        self.f_winners = Func(
            F("winner_count"), function="CAST", template=template
        )
        self.per_seat = ExpressionWrapper(
            self.f_winners / self.f_candidates, output_field=FloatField()
        )

    def run(self):
        print()
        print()
        print()
        title = f"{self.date}: {self.name}, {self.election_type} elections"
        suffix = ""
        if self.nation:
            suffix = f" ({settings.NATION_LABEL[self.nation]})"

        if self.elected:
            suffix = f", elected only{suffix}"

        title = f"{title}{suffix}"

        print(title)
        print("=" * len(title))
        print()
        print(self.report())


def report_runner(name, date, **kwargs):
    this_module = sys.modules[__name__]
    if hasattr(this_module, name):
        return getattr(this_module, name)(date=date, **kwargs).run()
    else:
        raise ValueError(
            "{} is unknown. Pick one of: {}".format(
                name,
                "\n\t".join(
                    [
                        x
                        for x in dir(this_module)
                        if hasattr(getattr(this_module, x), "__base__")
                        and getattr(this_module, x).__base__ == BaseReport
                    ]
                ),
            )
        )


class NumberOfCandidates(BaseReport):

    name = "Number of candidates standing"

    def get_qs(self):
        return (
            self.membership_qs.values("ballot__election__for_post_role")
            .annotate(seats=Count("pk"))
            .order_by()
        )

    def report(self):
        report = []
        for election_type in self.get_qs():
            report.append(
                "{}\t{}".format(
                    election_type["ballot__election__for_post_role"],
                    election_type["seats"],
                )
            )
        return "\n".join(report)


class NumberOfSeats(BaseReport):
    name = "Number of seats"

    def get_qs(self):
        return self.ballot_qs.values("election__for_post_role").annotate(
            seats=Sum("winner_count")
        )

    def report(self):
        report = []
        for election_type in self.get_qs():
            report.append(
                "{}\t{}".format(
                    election_type["election__for_post_role"],
                    election_type["seats"],
                )
            )
        return "\n".join(report)


class CandidatesPerParty(BaseReport):
    name = "Candidates per party"

    def get_qs(self):
        return (
            self.membership_qs.values("party__name", "party__register")
            .annotate(membership_count=Count("party_id"))
            .order_by("-membership_count")
        )

    def report(self):
        report = ["Party Name\tParty Register\tCandidates\tPercent of seats"]

        total_seats = self.ballot_qs.aggregate(seats=Sum("winner_count"))[
            "seats"
        ]

        for party in self.get_qs():
            report.append(
                "\t".join(
                    [
                        str(v)
                        for v in [
                            party["party__name"],
                            party["party__register"],
                            party["membership_count"],
                            round(
                                float(
                                    party["membership_count"]
                                    / total_seats
                                    * 100
                                ),
                                2,
                            ),
                        ]
                    ]
                )
            )
        return "\n".join(report)


class WardsContestedPerParty(BaseReport):
    def get_qs(self):
        # get candidates distinct by party and ballot
        qs = self.membership_qs.distinct("party_id", "ballot_id").order_by()
        # use the pk's to create a new queryset to work with
        # we need the new qs so we can use annotate later
        qs = qs.values_list("pk")
        qs = Membership.objects.filter(pk__in=qs)
        # count the number of candidates per party now we have removed
        # candidacies where multiple candidates are standing per party
        qs = qs.values("party__name", "party__register")
        qs = qs.annotate(membership_count=Count("party_id"))
        qs = qs.order_by("-membership_count")
        return qs

    @property
    def name(self):
        total_wards = self.ballot_qs.count()
        return f"Wards contested per party ({total_wards})"

    def report(self):
        report = [
            "Party Name\tParty Register\tCandidates standing\tPercent of wards"
        ]

        total_ballots = self.ballot_qs.count()
        for party in self.get_qs():
            report.append(
                "\t".join(
                    [
                        str(v)
                        for v in [
                            party["party__name"],
                            party["party__register"],
                            party["membership_count"],
                            round(
                                float(
                                    party["membership_count"]
                                    / total_ballots
                                    * 100
                                ),
                                2,
                            ),
                        ]
                    ]
                )
            )
        return "\n".join(report)


class UncontestedBallots(BaseReport):
    name = "Uncontested Ballots"

    def get_qs(self):
        return (
            self.ballot_qs.annotate(memberships_count=Count("membership"))
            .filter(winner_count__gte=F("memberships_count"))
            .filter(candidates_locked=True)
            .order_by("ballot_paper_id")
        )

    def report(self):
        report_list = []
        qs = self.get_qs()
        report_list.append(["{} uncontested seats".format(qs.count())])

        report_list.append("\n")
        for ballot in qs:

            for membership in ballot.membership_set.all():
                report_list.append(
                    [
                        ballot.ballot_paper_id,
                        membership.person.name,
                        membership.party.name,
                    ]
                )

        return "\n".join(["\t".join(r) for r in report_list])


class NcandidatesPerSeat(BaseReport):
    def __init__(self, date, n=2, **kwargs):
        self.n = 1 / n
        super().__init__(date, **kwargs)

    @property
    def name(self):
        return "Wards with fewer than {} candidates per seat".format(1 / self.n)

    def get_qs(self):
        return (
            self.ballot_qs.annotate(candidates=Count("membership"))
            .annotate(per_seat=self.per_seat)
            .filter(per_seat__gt=self.n)
        )

    def report(self):
        qs = self.get_qs()
        report_list = []
        headers = [
            "Ballot Paper ID",
            "Candidate Name",
            "Party Name",
            "Seats per candidate",
            "Seats Contested",
            "Will Win",
        ]
        report_list.append(headers)
        for ballot in qs:
            if ballot.cancelled is True:
                continue

            parties = (
                ballot.membership_set.all()
                .values_list("party__name", flat=True)
                .distinct()
            )

            if parties.count() > ballot.winner_count:
                continue

            parties = Counter(parties)
            will_win, will_win_seats = parties.most_common(1)[0]
            parties[will_win] -= ballot.winner_count
            will_win_seats -= sum(parties.values())
            for membership in ballot.membership_set.all():
                is_a_winner = False
                if membership.party.name == will_win and will_win_seats:
                    is_a_winner = True
                    will_win_seats -= 1

                report_list.append(
                    [
                        ballot.ballot_paper_id,
                        membership.person.name,
                        membership.party.name,
                        ballot.per_seat,
                        ballot.winner_count,
                        is_a_winner,
                    ]
                )

        return "\n".join(["\t".join([str(c) for c in r]) for r in report_list])


class TwoWayRace(BaseReport):
    name = "Number of two-way fights"

    def get_qs(self):
        return (
            self.ballot_qs.values("ballot_paper_id")
            .annotate(candidates=Count("membership"))
            .annotate(
                party_count=Count("membership__party__name", distinct=True)
            )
            .filter(party_count=2)
            .order_by("ballot_paper_id")
        )

    def report(self):
        qs = self.get_qs()
        report_list = []
        headers = [
            "Ballot Paper ID",
            "Num candidates",
            "Party Name",
            "Party Name",
        ]
        report_list.append(headers)
        for ballot in qs:
            ballot_obj = Ballot.objects.get(
                ballot_paper_id=ballot["ballot_paper_id"]
            )
            parties = []

            for membership in ballot_obj.membership_set.distinct(
                "party_id"
            ).order_by("party_id"):
                parties.append(membership.party.name)

            report_list.append(
                [ballot["ballot_paper_id"], ballot["candidates"]] + parties
            )

        return "\n".join(["\t".join([str(c) for c in r]) for r in report_list])


class TwoWayRaceForNewParties(TwoWayRace):
    def get_qs(self):
        qs = super().get_qs()
        year = self.date.split("-")[0]
        qs = qs.filter(membership__party__date_registered__year=year)
        return qs


class TwoWayRaceForNcandidates(TwoWayRace):
    def get_qs(self):
        n = 6
        return super().get_qs().filter(candidates__gte=n)


class MostPerSeat(BaseReport):
    name = "Highest number of candidates per seats"

    def get_qs(self):
        return (
            self.ballot_qs.annotate(candidates=Count("membership"))
            .annotate(per_seat=self.per_seat)
            .order_by("per_seat")
        )

    def report(self):
        qs = self.get_qs()
        report_list = [
            ["Ballot paper ID", "num candidates", "per seat", "winners"]
        ]
        for x in qs[:10]:
            report_list.append(
                [x.ballot_paper_id, x.candidates, x.per_seat, x.winner_count]
            )
        return "\n".join(["\t".join([str(c) for c in r]) for r in report_list])


class NewParties(BaseReport):
    name = "Parties formed this year standing candidates"

    def get_qs(self):
        return self.membership_qs.filter(
            party__date_registered__year=self.date.split("-")[0]
        ).order_by("party_id")

    def report(self):
        qs = self.get_qs()
        report_list = []
        headers = ["Party Name", "Ballot Paper ID", "Candidate name"]
        report_list.append(headers)
        for membership in qs:
            report_list.append(
                [
                    membership.party.name,
                    membership.ballot.ballot_paper_id,
                    membership.person.name,
                ]
            )
        return "\n".join(["\t".join([str(c) for c in r]) for r in report_list])


class GenderSplitByDate(BaseReport):
    name = "GenderSplit By Date"

    def get_qs(self):
        return (
            self.membership_qs.values("person__gender_guess__gender")
            .order_by("person__gender_guess__gender")
            .annotate(gender_count=Count("person__gender_guess__gender"))
        )

    def report(self):
        qs = self.get_qs()
        report_list = []
        headers = ["Gender", "Gender Count"]
        report_list.append(headers)
        for gender in qs:
            report_list.append(
                [gender["person__gender_guess__gender"], gender["gender_count"]]
            )
        return "\n".join(["\t".join([str(c) for c in r]) for r in report_list])


class NamesAndGenderGuessOnly(BaseReport):
    """
    Filters the membership QS to only include candidates where a gender value
    was not entered by a volunteer/user, then return the name of each candidate
    and the gender that was guessed using the "people_guess_gender" management
    command.
    Originally requested by Fawcett Society.
    """

    name = "Names and guessed gender, based only on name entered"

    def get_qs(self):
        return (
            self.membership_qs.filter(person__gender="")
            .exclude(person__gender_guess__isnull=True)
            .order_by("person__gender_guess__gender")
            .select_related("ballot", "person", "person__gender_guess")
        )

    def report(self):
        qs = self.get_qs()
        report_list = []
        headers = ["Name", "Guessed Gender", "Person ID", "Ballot URL", "Party"]
        report_list.append(headers)
        for membership in qs:
            report_list.append(
                [
                    membership.person.name,
                    membership.person.gender_guess.gender,
                    membership.person.pk,
                    membership.ballot.ballot_paper_id,
                    membership.party.name,
                ]
            )
        return "\n".join(["\t".join([str(c) for c in r]) for r in report_list])


class GenderSplitByParty(BaseReport):
    name = "Gender Split By Party"

    def get_qs(self):
        return (
            self.membership_qs.values(
                "person__gender_guess__gender", "party__name"
            )
            .annotate(gender_count=Count("person__gender_guess__gender"))
            .order_by("party__name")
        )

    def report(self):
        qs = self.get_qs()
        report_list = []
        headers = ["Gender", "Gender Count", "Party Name"]
        report_list.append(headers)
        for gender in qs:
            report_list.append(
                [
                    gender["person__gender_guess__gender"],
                    gender["gender_count"],
                    gender["party__name"],
                ]
            )
        return "\n".join(["\t".join([str(c) for c in r]) for r in report_list])


class GenderSplitByRegion(BaseReport):
    name = "Gender Split By Region"

    def get_qs(self):
        return (
            self.membership_qs.values(
                "person__gender_guess__gender", "ballot__tags__NUTS1__value"
            )
            .annotate(gender_count=Count("person__gender_guess__gender"))
            .order_by("ballot__tags__NUTS1__value")
        )

    def report(self):
        qs = self.get_qs()
        report_list = []
        headers = ["Gender", "Gender Count", "Region"]
        report_list.append(headers)
        for gender in qs:
            report_list.append(
                [
                    gender["person__gender_guess__gender"],
                    gender["gender_count"],
                    gender["ballot__tags__NUTS1__value"],
                ]
            )
        return "\n".join(["\t".join([str(c) for c in r]) for r in report_list])


class GenderSplitByElectionType(BaseReport):
    name = "Gender Split By Election Type"

    def get_qs(self):
        return (
            self.membership_qs.values(
                "person__gender_guess__gender",
                "ballot__election__for_post_role",
            )
            .annotate(gender_count=Count("person__gender_guess__gender"))
            .order_by("ballot__election__for_post_role")
        )

    def report(self):
        qs = self.get_qs()
        report_list = []
        headers = ["Gender", "Gender Count", "Party Name"]
        report_list.append(headers)
        for gender in qs:
            report_list.append(
                [
                    gender["person__gender_guess__gender"],
                    gender["gender_count"],
                    gender["ballot__election__for_post_role"],
                ]
            )
        return "\n".join(["\t".join([str(c) for c in r]) for r in report_list])


class GenderSplitBySeatsContested(BaseReport):
    name = "Gender Split By Seats Contested"

    def get_qs(self):
        return (
            self.membership_qs.values(
                "person__gender_guess__gender", "ballot__winner_count"
            )
            .annotate(gender_count=Count("person__gender_guess__gender"))
            .order_by("ballot__winner_count")
        )

    def report(self):
        qs = self.get_qs()
        report_list = []
        headers = ["Seats Contested", "F", "M", "Ratio"]
        report_list.append(headers)
        grouped_rows = {}
        for gender in qs:
            if not grouped_rows.get(gender["ballot__winner_count"]):
                grouped_rows[gender["ballot__winner_count"]] = {}
            grouped_rows[gender["ballot__winner_count"]][
                gender["person__gender_guess__gender"]
            ] = gender["gender_count"]
        for seats_contested, data in grouped_rows.items():
            ratio = (
                f'{round(data["M"] / data["F"],2)}'
                f':{round(data["F"] / data["F"],2)}'
            )
            report_list.append([seats_contested, data["F"], data["M"], ratio])

        return "\n".join(["\t".join([str(c) for c in r]) for r in report_list])


class SingleGenderedBallots(BaseReport):
    name = "Single Gender Wards"

    def get_qs(self):
        return (
            self.membership_qs.values("ballot__ballot_paper_id")
            .order_by("ballot__ballot_paper_id")
            .annotate(
                genders=Count("person__gender_guess__gender", distinct=True)
            )
            .filter(genders=1)
            .values_list("ballot__ballot_paper_id", flat=True)
        )

    def report(self):
        report_list = []
        headers = ["Label", "Count", "Sample"]
        report_list.append(headers)
        report_list.append(
            [
                "All Single gender ballots",
                self.get_qs().count(),
                "\t".join(self.get_qs()[:10]),
            ]
        )
        for gender in ["F", "M"]:
            ballots = self.get_qs()
            qs = (
                Membership.objects.order_by("ballot__ballot_paper_id")
                .distinct("ballot__ballot_paper_id")
                .filter(
                    person__gender_guess__gender=gender,
                    ballot__ballot_paper_id__in=ballots,
                )
                .values_list("ballot__ballot_paper_id", flat=True)
            )
            report_list.append(
                [f"All {gender} gender ballots", qs.count(), "\t".join(qs[:10])]
            )

        return "\n".join(["\t".join([str(c) for c in r]) for r in report_list])


class PartyMovers(BaseReport):
    name = "Party movers"

    def get_qs(self):
        people_for_date = Membership.objects.filter(
            ballot__election__election_date=self.date
        ).values("person_id")
        return (
            Membership.objects.filter(person__in=people_for_date)
            .values("person_id", "person__name")
            .annotate(party_count=Count("party_id", distinct=True))
            .order_by("person_id")
            .filter(party_count__gt=1)
        )

    def report(self):
        qs = self.get_qs()
        report_list = []
        headers = ["Person ID", "Person Name", "Party Count"]
        report_list.append(headers)
        for person_dict in qs:
            person = Person.objects.get(pk=person_dict["person_id"])
            memberships = person.memberships.all().order_by(
                "ballot__election__election_date"
            )
            id_set = set([m.party.ec_id for m in memberships])
            if id_set == {"PP53", "joint-party:53-119"}:
                continue
            report_list.append(
                [
                    person_dict["person_id"],
                    person_dict["person__name"],
                    person_dict["party_count"],
                ]
                + list(id_set)
            )
        return "\n".join(["\t".join([str(c) for c in r]) for r in report_list])


class RegionalNumCandidatesPerSeat(BaseReport):
    name = "Number of candidates per seat per region"

    def report(self):
        report_list = []
        headers = [
            "Region Name",
            "Region Code",
            "Num Seats",
            "Num Candidates",
            "Num Candidates Per Seats",
        ]
        report_list.append(headers)
        for region in region_choices():
            code = region[0]
            name = region[1]
            qs = self.ballot_qs.by_region(code=code)
            candidates = (
                qs.aggregate(Count("membership"))["membership__count"] or 0
            )
            seats_contested = (
                qs.aggregate(Sum("winner_count"))["winner_count__sum"] or 0
            )

            try:
                candidates_per_seat = round(candidates / seats_contested, 2)
            except ZeroDivisionError:
                candidates_per_seat = 0

            report_list.append(
                [name, code, seats_contested, candidates, candidates_per_seat]
            )

        return "\n".join(
            ["\t".join([str(cell) for cell in row]) for row in report_list]
        )


class SmallPartiesCandidatesCouncilAreas(BaseReport):
    PARTIES = [
        "Reform UK",
        "Trade Unionist and Socialist Coalition",
        "UK Independence Party (UKIP)",
        "Freedom Alliance- Integrity, Society, Economy",
        "Social Democratic Party",
        "The For Britain Movement",
    ]

    name = (
        "Number of candidates stood in each council area for smaller candidates"
    )

    def get_qs(self, parties=None):
        parties = parties or self.PARTIES
        return Party.objects.filter(name__in=parties, register="GB").distinct()

    def report(self):
        report_list = []
        headers = [
            "Party Name",
            "Council Area",
            "Total Candidates For Council Area",
        ]
        report_list.append(headers)
        parties = self.get_qs()

        for party in parties:
            candidacies = self.membership_qs.filter(party=party)
            elections_for_party = (
                candidacies.order_by("ballot__election__name")
                .values_list("ballot__election__slug", flat=True)
                .distinct()
            )
            for election_slug in elections_for_party:
                count = candidacies.filter(
                    ballot__election__slug=election_slug
                ).count()
                council_area = election_slug.split(".")[1]
                report_list.append([party.name, council_area.title(), count])

        return "\n".join(
            ["\t".join([str(cell) for cell in row]) for row in report_list]
        )


class NumCandidatesStandingInMultipleSeats(BaseReport):

    name = "Candidates standing in multiple seats"

    def get_qs(self):
        """
        Get all distinct people standing
        """
        people_ids = self.membership_qs.values_list(
            "person", flat=True
        ).distinct()
        people = Person.objects.filter(pk__in=people_ids)

        membership_filter = Q(
            memberships__ballot__election__election_date=self.date
        )
        if self.election_type != "all":
            membership_filter = membership_filter & Q(
                memberships__ballot__election__slug__startswith=self.election_type
            )

        if self.elected:
            membership_filter = membership_filter & Q(memberships__elected=True)

        current_candidacies = Count(
            "memberships", filter=membership_filter, distinct=True
        )
        return people.annotate(num_candidacies=current_candidacies)

    def report(self):
        report_list = []
        headers = [
            "Num Candidacies",
            "Total Candidates standing for this number of candidacies",
        ]
        report_list.append(headers)
        qs = self.get_qs()
        # very arbritary safeguard but im assuming you would never have someone
        # stand on this many ballots for the same election type and date
        for num in range(1, 10):
            count = qs.filter(num_candidacies=num).count()
            if count == 0:
                break
            report_list.append([num, count])

        return "\n".join(
            ["\t".join([str(cell) for cell in row]) for row in report_list]
        )


class PeopleWithMultipleCandidaciesDetailed(
    NumCandidatesStandingInMultipleSeats
):
    """
    Builds report with full details of people standing on more than one ballot
    """

    name = "People with multiple candidacies"

    def get_qs(self):
        qs = super().get_qs()
        qs = qs.filter(num_candidacies__gt=1)

        filters = {"ballot__election__election_date": self.date}
        if self.elected:
            filters["elected"] = True

        return qs.prefetch_related(
            Prefetch(
                "memberships", queryset=Membership.objects.filter(**filters)
            )
        )

    def report(self):
        report_list = []
        headers = ["ID", "Name", "Num candidacies", "Ballot ID's"]
        report_list.append(headers)
        for person in self.get_qs():
            ballot_ids = ", ".join(
                person.memberships.values_list(
                    "ballot__ballot_paper_id", flat=True
                )
            )
            row = [person.pk, person.name, person.num_candidacies, ballot_ids]
            report_list.append(row)

        return "\n".join(
            ["\t".join([str(cell) for cell in row]) for row in report_list]
        )


class NumCandidatesStandingInMultipleSeatsPerGender(
    NumCandidatesStandingInMultipleSeats
):

    name = "Num candidates standing in multiple per seats, per gender"

    def report(self):

        genders = (
            self.membership_qs.values_list(
                "person__gender_guess__gender", flat=True
            )
            .order_by("person__gender_guess__gender")
            .distinct()
        )

        report_list = []
        headers = ["Gender", "Num Candidacies", "Num people standing"]
        report_list.append(headers)
        qs = self.get_qs()
        # very arbritary safeguard but im assuming you would never have someone
        # stand on this many ballots for the same election type and date
        for num in range(1, 10):
            for gender in genders:
                count = (
                    qs.filter(gender_guess__gender=gender)
                    .filter(num_candidacies=num)
                    .count()
                )
                report_list.append([gender, num, count])

        return "\n".join(
            ["\t".join([str(cell) for cell in row]) for row in report_list]
        )


class CommonFirstNames(BaseReport):

    name = "Common first names"

    def get_qs(self):
        """
        Get all distinct people standing
        """
        return self.membership_qs

    def collect_names(self, label, qs):
        all_names = qs.values_list("person__name", flat=True)
        all_first_names = [name.split(" ")[0].title() for name in all_names]
        collector = collections.Counter(all_first_names)
        for name, count in collector.most_common(30):
            yield [label, name, count]

    def report(self):
        report_list = []
        headers = ["Type", "Name", "Count"]
        report_list.append(headers)
        qs = self.get_qs()
        if self.nation:
            label = f"Across {settings.NATION_LABEL[self.nation]}"
        else:
            label = f"On {self.date}"
        for row in self.collect_names(label, qs):
            report_list.append(row)

        # For all parties standing:
        parties = (
            self.membership_qs.values_list("party__ec_id", "party_name")
            .distinct("party_name")
            .order_by("party_name")
        )

        for party in parties:
            label = f"{party[1]}"
            if self.nation:
                label = f"{label} ({settings.NUTS_TO_NATION[self.nation]} only)"
            qs = self.get_qs().filter(party__ec_id=party[0])
            for row in self.collect_names(label, qs):
                report_list.append(row)

        for region in region_choices():
            label = f"{region[1]}"
            qs = self.get_qs().filter(ballot__tags__NUTS1__key=region[0])
            for row in self.collect_names(label, qs):
                report_list.append(row)

        return "\n".join(
            ["\t".join([str(cell) for cell in row]) for row in report_list]
        )


class CommonLastNames(CommonFirstNames):

    name = "Common last names"

    def collect_names(self, label, qs):
        all_names = qs.values_list("person__name", flat=True)
        all_first_names = [name.split(" ")[-1].title() for name in all_names]
        collector = collections.Counter(all_first_names)
        for name, count in collector.most_common(30):
            yield [label, name, count]


class CandidatesWithWithoutStatement(BaseReport):

    name = "Candidates with or without statement"

    def get_qs(self):
        return self.membership_qs.select_related("person")

    def report(self):
        report_list = []
        headers = ["", "Number", "%"]
        report_list.append(headers)
        qs = self.get_qs()
        all_candidates = qs.count()
        num_with_statement = qs.exclude(person__biography="").count()
        num_without_statement = qs.filter(person__biography="").count()
        report_list.append(
            [
                "With statement",
                num_with_statement,
                round((num_with_statement / all_candidates) * 100),
            ]
        )
        report_list.append(
            [
                "Without statement",
                num_without_statement,
                round((num_without_statement / all_candidates) * 100),
            ]
        )
        return "\n".join(
            ["\t".join([str(cell) for cell in row]) for row in report_list]
        )


ALL_REPORT_CLASSES = []
for x in list(locals().values()):
    if type(x) == type and issubclass(x, BaseReport):
        if x.__name__ == "BaseReport":
            continue
        ALL_REPORT_CLASSES.append(x.__name__)
