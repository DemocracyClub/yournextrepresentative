"""
Highest number of candidates per seats & longest ballots (most parties contesting a seat?)
Geography – where are parties standing lots/no candidates - where are independents strongest, etc
Maybe strongest region groups (e.g. are Bath independents standing everywhere in bath?)
Gender
New parties
"""

import sys
from collections import Counter

from django.db.models import Count, ExpressionWrapper, F, FloatField, Func, Sum

from candidates.models import Ballot
from elections.filters import region_choices
from people.models import Person
from popolo.models import Membership


ALL_REPORT_CLASSES = [
    "NumberOfCandidates",
    "NumberOfSeats",
    "CandidatesPerParty",
    "UncontestedBallots",
    "NcandidatesPerSeat",
    "TwoWayRace",
    "TwoWayRaceForNewParties",
    "TwoWayRaceForNcandidates",
    "MostPerSeat",
    "NewParties",
    "GenderSplit",
    "PartyMovers",
    "RegionalNumCandidatesPerSeat",
]


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
    def __init__(self, date, election_type=None, register=None):
        self.date = date
        election_type = election_type or "local"
        register = register or "GB"

        self.ballot_qs = (
            Ballot.objects.filter(election__election_date=self.date)
            .filter(ballot_paper_id__startswith=election_type)
            # as discussed with Peter, dont exclude all by elections this year
            # only those in Wales/Scotland
            # .exclude(ballot_paper_id__contains=".by.")
            .exclude(ballot_paper_id__in=EXCLUSION_IDS)
            .filter(post__party_set__slug=register.lower())
            .exclude(cancelled=True)
            .exclude(membership=None)
        )

        self.membership_qs = (
            Membership.objects.filter(ballot__election__election_date=self.date)
            .filter(ballot__ballot_paper_id__startswith=election_type)
            .filter(ballot__post__party_set__slug=register.lower())
            # as discussed with Peter, dont exclude all by elections this year
            # only those in Wales/Scotland
            # .exclude(ballot__ballot_paper_id__contains=".by.")
            .exclude(ballot__ballot_paper_id__in=EXCLUSION_IDS)
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
        title = "{}: {}".format(self.date, self.name)
        print(title)
        print("=" * len(title))
        print()
        print(self.report())


def report_runner(name, date, election_type=None, register=None):
    this_module = sys.modules[__name__]
    if hasattr(this_module, name):
        return getattr(this_module, name)(
            date=date, election_type=election_type, register=register
        ).run()
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

        total_seats = Ballot.objects.filter(
            election__election_date=self.date
        ).aggregate(seats=Sum("winner_count"))["seats"]

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
        for ballot in qs:
            if ballot.cancelled is True:
                continue

            parties = Counter(
                ballot.membership_set.all().values_list(
                    "party__name", flat=True
                )
            )
            will_win, will_win_seats = parties.most_common(1)[0]
            del parties[will_win]
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
        qs = qs.filter(membership__party__date_registered__year="2019")
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
        report_list = [[]]
        for membership in qs:
            report_list.append(
                [
                    membership.party.name,
                    membership.ballot.ballot_paper_id,
                    membership.person.name,
                ]
            )
        return "\n".join(["\t".join([str(c) for c in r]) for r in report_list])


class GenderSplit(BaseReport):
    name = "Gender Split"

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
        for gender in qs:
            report_list.append(
                [
                    gender["person__gender_guess__gender"],
                    gender["gender_count"],
                    gender["party__name"],
                ]
            )
        return "\n".join(["\t".join([str(c) for c in r]) for r in report_list])


class PartyMovers(BaseReport):
    name = "Party movers"

    def get_qs(self):
        people_for_date = Membership.objects.filter(
            ballot__election__election_date=self.date
        ).values("person_id")
        print(people_for_date)
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
        for person_dict in qs:
            person = Person.objects.get(pk=person_dict["person_id"])
            memberships = person.memberships.all().order_by(
                "ballot__election__election_date"
            )
            id_set = set([m.party.ec_id for m in memberships])
            if id_set == set(["PP53", "joint-party:53-119"]):
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
        report_list = [
            [
                "Region Name",
                "Region Code",
                "Num Seats",
                "Num Candidates",
                "Num Candidates Per Seats",
            ]
        ]
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
