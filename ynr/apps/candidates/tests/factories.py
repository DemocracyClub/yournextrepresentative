import re
from datetime import timedelta

import factory
import faker
from slugify import slugify

from .dates import FOUR_YEARS_IN_DAYS, date_in_near_future

faker_factory = faker.Factory.create()


class PartySetFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = "candidates.PartySet"


class ParliamentaryChamberFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = "popolo.Organization"

    name = "House of Commons"
    slug = "commons"


class BaseElectionFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = "elections.Election"
        abstract = True

    slug = factory.LazyAttribute(lambda o: "sp.%s" % o.election_date)

    for_post_role = "Member of the Scottish Parliament"
    winner_membership_role = None
    candidate_membership_role = "Candidate"
    election_date = date_in_near_future
    name = "Scottish Parliamentary elections"
    current = True
    use_for_candidate_suggestions = False
    party_lists_in_use = False
    default_party_list_members_to_show = 0
    show_official_documents = True
    ocd_division = ""
    description = ""


class ElectionFactory(BaseElectionFactory):
    class Meta:
        model = "elections.Election"


class EarlierElectionFactory(BaseElectionFactory):
    class Meta:
        model = "elections.Election"

    slug = "earlier-general-election"
    name = "Earlier General Election"
    election_date = date_in_near_future - timedelta(days=FOUR_YEARS_IN_DAYS)
    current = False
    use_for_candidate_suggestions = True


class PostFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = "popolo.Post"

    role = "Member of Parliament"
    slug = factory.LazyAttribute(lambda o: slugify(o.label))
    identifier = factory.LazyAttribute(lambda o: slugify(o.label))
    label = "Sheffield, Hallam"
    organization = factory.SubFactory(
        "candidates.tests.factories.OrganizationFactory"
    )
    territory_code = "ENG"

    @factory.post_generation
    def elections(self, create, extracted, **kwargs):
        if not create:
            return
        if extracted:
            for election in extracted:
                if re.search(r"\d\d\d\d-\d\d-\d\d$", election.slug):
                    parts = election.slug.split(".")
                    parts.insert(-1, self.slug)
                    ballot_paper_id = ".".join(parts)
                else:
                    ballot_paper_id = "{}.{}".format(election.slug, self.slug)

                BallotPaperFactory.create(
                    post=self,
                    election=election,
                    ballot_paper_id=ballot_paper_id,
                    winner_count=1,
                )


class BallotPaperFactory(factory.django.DjangoModelFactory):
    election = factory.SubFactory(ElectionFactory)
    post = factory.SubFactory(PostFactory)

    class Meta:
        model = "candidates.Ballot"

    @factory.lazy_attribute_sequence
    def ballot_paper_id(self, n):
        """
        Builds a unique string to use as a ballot paper ID.
        TODO make this more realistic like actual ballot paper ID's.
        """
        slug = faker_factory.slug()
        return f"{slug}-{n}"


class OrganizationFactory(factory.django.DjangoModelFactory):
    name = "House of Commons of the United Kingdom"

    class Meta:
        model = "popolo.Organization"


class MembershipFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = "popolo.Membership"

    role = "Candidate"
