from candidates.models import Ballot, PartySet
from django.core.management import BaseCommand
from elections.models import Election
from parties.models import Party
from people.models import Person
from popolo.models import Membership, Organization, Post

GB_REGISTER = PartySet.objects.get(slug="gb")

POSTS = {
    "richmond-yorks": {
        "role": "Member of Parliament",
        "party_set": GB_REGISTER,
        "label": "Richmond (Yorks)",
    },
    "south-west-norfolk": {
        "role": "Member of Parliament",
        "party_set": GB_REGISTER,
        "label": "South West Norfolk",
    },
    "uxbridge-and-south-ruislip": {
        "role": "Member of Parliament",
        "party_set": GB_REGISTER,
        "label": "Uxbridge and South Ruislip",
    },
    "maidenhead": {
        "role": "Member of Parliament",
        "party_set": GB_REGISTER,
        "label": "Maidenhead",
    },
}

ELECTIONS = {
    "parl.richmond-yorks.2024-05-02": {
        "current": True,
        "people": [
            {
                "name": "Rishi Sunak",
                "party": "PP52",
            },
            {
                "name": "John Yorke",
                "party": "PP63",
            },
            {
                "name": "Nick Jardine",
                "party": "ynmp-party:2",
            },
            {
                "name": "Thom Kirkwood",
                "party": "PP53",
            },
            {
                "name": "Philip Michael Knowles",
                "party": "PP90",
            },
            {
                "name": "Laurence Warwick Waterhouse",
                "party": "PP2055",
            },
        ],
    },
    "parl.south-west-norfolk.2023-05-04": {
        "current": True,
        "people": [
            {
                "name": "Elizabeth Truss",
                "party": "PP52",
                "votes_cast": 32894,
                "elected": True,
            },
            {
                "name": "Peter Smith",
                "party": "PP53",
                "votes_cast": 14582,
                "elected": False,
            },
            {
                "name": "Stephen Gordon",
                "party": "PP90",
                "votes_cast": 2365,
                "elected": False,
            },
            {
                "name": "Dave Williams",
                "party": "PP85",
                "votes_cast": 2575,
                "elected": False,
            },
        ],
    },
    "parl.uxbridge-and-south-ruislip.2019-12-12": {
        "current": True,
        "people": [
            {
                "name": "Boris Johnson",
                "party": "PP52",
                "votes_cast": 25351,
                "elected": True,
            },
            {
                "name": "Mark Keir",
                "party": "PP63",
                "votes_cast": 1090,
                "elected": False,
            },
            {
                "name": "Alfie John Utting",
                "party": "ynmp-party:2",
                "votes_cast": 44,
                "elected": False,
            },
            {
                "name": 'Bobby "Elmo" Smith',
                "party": "ynmp-party:2",
                "votes_cast": 8,
                "elected": False,
            },
            {
                "name": "Count Binface",
                "party": "ynmp-party:2",
                "votes_cast": 69,
                "elected": False,
            },
            {
                "name": "Norma Burke",
                "party": "ynmp-party:2",
                "votes_cast": 22,
                "elected": False,
            },
            {
                "name": "William John Tobin",
                "party": "ynmp-party:2",
                "votes_cast": 5,
                "elected": False,
            },
            {
                "name": 'Yace "Interplanetary Time Lord" Yogenstein',
                "party": "ynmp-party:2",
                "votes_cast": 23,
                "elected": False,
            },
            {
                "name": "Ali Milani",
                "party": "PP53",
                "votes_cast": 18141,
                "elected": False,
            },
            {
                "name": "Jo Humphreys",
                "party": "PP90",
                "votes_cast": 3026,
                "elected": False,
            },
            {
                "name": "Lord Buckethead",
                "party": "PP66",
                "votes_cast": 125,
                "elected": False,
            },
            {
                "name": "Geoffrey Courtenay",
                "party": "PP85",
                "votes_cast": 283,
                "elected": False,
            },
        ],
    },
    "parl.maidenhead.2017-06-08": {
        "current": True,
        "people": [
            {
                "name": "Andrew Knight",
                "party": "PP616",
                "votes_cast": 282,
                "elected": False,
            },
            {
                "name": "Edmonds Victor",
                "party": "PP79",
                "votes_cast": 69,
                "elected": False,
            },
            {
                "name": "Theresa May",
                "party": "PP52",
                "votes_cast": 37718,
                "elected": True,
            },
            {
                "name": "Derek Wall",
                "party": "PP63",
                "votes_cast": 907,
                "elected": False,
            },
            {
                "name": 'Bobby "Elmo" Smith',
                "party": "ynmp-party:2",
                "votes_cast": 3,
                "elected": False,
            },
            {
                "name": "Grant Smith",
                "party": "ynmp-party:2",
                "votes_cast": 152,
                "elected": False,
            },
            {
                "name": "Lord Buckethead",
                "party": "ynmp-party:2",
                "votes_cast": 249,
                "elected": False,
            },
            {
                "name": "Yemi Hailemariam",
                "party": "ynmp-party:2",
                "votes_cast": 16,
                "elected": False,
            },
            {
                "name": "Pat McDonald",
                "party": "PP53",
                "votes_cast": 11261,
                "elected": False,
            },
            {
                "name": "Tony Hill",
                "party": "PP90",
                "votes_cast": 6540,
                "elected": False,
            },
            {
                "name": "Julian Reid",
                "party": "PP2520",
                "votes_cast": 52,
                "elected": False,
            },
            {
                "name": "Howling Laud Hope",
                "party": "PP66",
                "votes_cast": 119,
                "elected": False,
            },
            {
                "name": "Gerard Batten",
                "party": "PP85",
                "votes_cast": 871,
                "elected": False,
            },
        ],
    },
}


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument("--no-input", action="store_true")

    def handle(self, *args, **options):
        if not options["no_input"]:
            confirm = self.boolean_input(
                """
            This command will create some FAKE elections. You don't want to run this on production, ever.

            Are you sure you want to continue?

            N/y
            """
            )

            if not confirm:
                return
        self.create_org()
        self.create_posts()
        self.create_elections()
        self.create_ballots()
        self.create_people()

    def boolean_input(self, question, default=None):
        result = input("%s " % question)
        if not result and default is not None:
            return default
        while len(result) < 1 or result[0].lower() not in "yn":
            result = input("Please answer yes or no: ")
        return result[0].lower() == "y"

    def create_org(self):
        self.organisation, _ = Organization.objects.get_or_create(
            name="House of Commons", classification="parl", slug="parl"
        )

    def create_posts(self):
        self.posts = {}
        for post_slug, post in POSTS.items():
            self.posts[post_slug] = Post.objects.get_or_create(
                slug=post_slug,
                organization=self.organisation,
                start_date="2010-05-06",
                role=post["role"],
                label=post["label"],
                party_set=post["party_set"],
                identifier=post_slug,
            )[0]

    def create_elections(self):
        self.elections = {}
        for election_id, election_data in ELECTIONS.items():
            parts = election_id.split(".")
            parts[1]
            date = parts[2]
            election_slug = f"parl.{date}"
            election_obj, created = Election.objects.update_or_create(
                slug=election_slug,
                election_date=date,
                defaults={
                    "current": election_data["current"],
                    "candidate_membership_role": "Candidate",
                    "for_post_role": "UK Parliament elections",
                    "show_official_documents": True,
                    "name": "UK General Election",
                    "party_lists_in_use": False,
                    "organization": self.organisation,
                },
            )
            self.elections[election_slug] = election_obj

    def create_ballots(self):
        self.ballots = {}
        for election_id, election_data in ELECTIONS.items():
            parts = election_id.split(".")
            post_slug = parts[1]
            election = self.elections[f"parl.{parts[-1]}"]
            self.ballots[election_id] = Ballot.objects.update_or_create(
                ballot_paper_id=election_id,
                defaults={
                    "election": election,
                    "post": self.posts[post_slug],
                },
            )[0]

    def create_people(self):
        for ballot_slug, ballot_data in ELECTIONS.items():
            for person in ballot_data.get("people", []):
                person_obj, _ = Person.objects.get_or_create(
                    name=person["name"]
                )
                party = Party.objects.get(ec_id=person["party"])
                Membership.objects.update_or_create(
                    person=person_obj,
                    party=party,
                    ballot=self.ballots[ballot_slug],
                )
