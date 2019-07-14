from datetime import timedelta
import re

import factory
import faker


from .dates import date_in_near_future, FOUR_YEARS_IN_DAYS

faker_factory = faker.Factory.create()


class PartySetFactory(factory.DjangoModelFactory):
    class Meta:
        model = "candidates.PartySet"


class ParliamentaryChamberFactory(factory.DjangoModelFactory):
    class Meta:
        model = "popolo.Organization"

    name = "House of Commons"
    slug = "commons"


class BaseElectionFactory(factory.DjangoModelFactory):
    class Meta:
        model = "elections.Election"
        abstract = True

    slug = "sp.2016-05-05"
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


class PostFactory(factory.DjangoModelFactory):
    class Meta:
        model = "popolo.Post"

    role = "Member of Parliament"

    @factory.post_generation
    def elections(self, create, extracted, **kwargs):
        if not create:
            return
        if extracted:
            for election in extracted:
                if re.search("\d\d\d\d-\d\d-\d\d$", election.slug):
                    parts = election.slug.split(".")
                    parts.insert(-1, self.slug)
                    ballot_paper_id = ".".join(parts)
                else:
                    ballot_paper_id = "{}.{}".format(election.slug, self.slug)

                PostExtraElectionFactory.create(
                    post=self,
                    election=election,
                    ballot_paper_id=ballot_paper_id,
                    winner_count=1,
                )


class PostExtraElectionFactory(factory.DjangoModelFactory):
    class Meta:
        model = "candidates.Ballot"


class OrganizationFactory(factory.DjangoModelFactory):
    class Meta:
        model = "popolo.Organization"


class MembershipFactory(factory.DjangoModelFactory):
    class Meta:
        model = "popolo.Membership"

    role = "Candidate"
