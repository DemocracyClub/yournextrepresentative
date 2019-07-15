from abc import abstractmethod, ABCMeta

from django.contrib.contenttypes.models import ContentType
from django.core.management import call_command

from datetime import date

import people.tests.factories
from . import factories
from parties.tests.factories import PartyFactory

EXAMPLE_PARTIES = [
    {
        "ec_id": "PP53",
        "legacy_slug": "party:53",
        "name": "Labour Party",
        "attr": "labour_party",
        "register": "GB",
    },
    {
        "ec_id": "PP90",
        "legacy_slug": "party:90",
        "name": "Liberal Democrats",
        "attr": "ld_party",
        "register": "GB",
    },
    {
        "ec_id": "PP63",
        "legacy_slug": "party:63",
        "name": "Green Party",
        "attr": "green_party",
        "register": "GB",
    },
    {
        "ec_id": "PP52",
        "legacy_slug": "party:52",
        "name": "Conservative Party",
        "attr": "conservative_party",
        "register": "GB",
    },
    {
        "ec_id": "PP39",
        "legacy_slug": "party:39",
        "name": "Sinn Féin",
        "attr": "sinn_fein",
        "register": "NI",
    },
]


class UK2015ExamplesMixin(object, metaclass=ABCMeta):
    def setUp(self):
        ContentType.objects.clear_cache()

    @classmethod
    def setUpTestData(cls):
        super(UK2015ExamplesMixin, cls).setUpTestData()
        cls.gb_parties = factories.PartySetFactory.create(
            slug="gb", name="Great Britain"
        )
        cls.ni_parties = factories.PartySetFactory.create(
            slug="ni", name="Northern Ireland"
        )
        cls.commons = factories.ParliamentaryChamberFactory.create()
        # Create the 2010 and 2015 general elections:
        cls.election = factories.ElectionFactory.create(
            slug="parl.2015-05-07",
            name="2015 General Election",
            for_post_role="Member of Parliament",
            organization=cls.commons,
        )
        cls.earlier_election = factories.EarlierElectionFactory.create(
            slug="parl.2010-05-06",
            name="2010 General Election",
            for_post_role="Member of Parliament",
            current=False,
            organization=cls.commons,
        )
        # Create some example parties:
        PartyFactory.reset_sequence()

        for party in EXAMPLE_PARTIES:
            p = PartyFactory(
                ec_id=party["ec_id"],
                name=party["name"],
                legacy_slug=party["legacy_slug"],
                register=party["register"],
            )
            setattr(cls, party["attr"], p)

        # Create some example posts as well:
        EXAMPLE_CONSTITUENCIES = [
            {
                "id": "14419",
                "name": "Edinburgh East",
                "country": "Scotland",
                "attr": "edinburgh_east_post",
            },
            {
                "id": "14420",
                "name": "Edinburgh North and Leith",
                "country": "Scotland",
                "attr": "edinburgh_north_post",
            },
            {
                "id": "65808",
                "name": "Dulwich and West Norwood",
                "country": "England",
                "attr": "dulwich_post",
            },
            {
                "id": "65913",
                "name": "Camberwell and Peckham",
                "country": "England",
                "attr": "camberwell_post",
            },
        ]
        for cons in EXAMPLE_CONSTITUENCIES:
            label = "Member of Parliament for {}".format(cons["name"])
            post = factories.PostFactory.create(
                elections=(cls.election, cls.earlier_election),
                organization=cls.commons,
                slug=cons["id"],
                label=label,
                party_set=cls.gb_parties,
                group=cons["country"],
            )

            setattr(cls, cons["attr"], post)

            ballot_attr_name = "{}_ballot".format(cons["attr"])
            ballot = post.ballot_set.get(election=cls.election)
            setattr(cls, ballot_attr_name, ballot)

            ballot_attr_name = "{}_ballot_earlier".format(cons["attr"])
            ballot = post.ballot_set.get(election=cls.earlier_election)
            setattr(cls, ballot_attr_name, ballot)

        # Also create a local election and post:
        cls.local_council = factories.OrganizationFactory.create(
            name="Maidstone", slug="local-authority:maidstone"
        )
        cls.local_election = factories.ElectionFactory.create(
            slug="local.maidstone.2016-05-05",
            organization=cls.local_council,
            name="Maidstone local election",
            for_post_role="Local Councillor",
            election_date=date(2016, 5, 5),
        )
        cls.local_post = factories.PostFactory.create(
            elections=(cls.local_election,),
            slug="DIW:E05005004",
            label="Shepway South Ward",
            party_set=cls.gb_parties,
            organization=cls.local_council,
        )

        cls.local_ballot = cls.local_post.ballot_set.get()

    def create_lots_of_candidates(self, election, parties_and_counts):
        posts = [
            self.edinburgh_east_post,
            self.edinburgh_north_post,
            self.dulwich_post,
            self.camberwell_post,
        ]
        created = 0
        for party, candidates_to_create in parties_and_counts:
            for i in range(candidates_to_create):
                person_id = int("{}00{}".format(election.pk, created + 1))
                person = people.tests.factories.PersonFactory.create(
                    id=person_id, name="John Doe {}".format(person_id)
                )
                factories.MembershipFactory.create(
                    person=person,
                    post=posts[created % len(posts)],
                    party=party,
                    post_election=election.ballot_set.get(
                        post=posts[created % len(posts)]
                    ),
                )
                created += 1
        call_command("parties_update_current_candidates")
