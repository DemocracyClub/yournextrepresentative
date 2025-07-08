from candidates.tests.factories import (
    BallotPaperFactory,
    ElectionFactory,
    OrganizationFactory,
    PostFactory,
)


class KirkleesBatleyEastMixin:
    def populate_kirklees_election_data(self):
        self.kirklees_council = OrganizationFactory(name="Kirklees Council")
        self.kirklees_eletion = ElectionFactory(
            slug="local.kirklees.2017-10-26"
        )
        self.batley_east_ward = PostFactory(
            label="Batley East", organization=self.kirklees_council
        )
        self.batley_east_ballot = BallotPaperFactory(
            ballot_paper_id="local.kirklees.batley-east.2017-10-26",
            post=self.batley_east_ward,
            election=self.kirklees_eletion,
            winner_count=1,
        )

    def setUp(self):
        super().setUp()
        self.populate_kirklees_election_data()
