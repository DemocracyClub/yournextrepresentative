from django_webtest import WebTest

from candidates.tests.factories import MembershipFactory, PersonFactory
from candidates.tests.uk_examples import UK2015ExamplesMixin


class TestAPI(UK2015ExamplesMixin, WebTest):
    def setUp(self):
        super().setUp()

        person = PersonFactory.create(id="2009", name="Tessa Jowell")
        dulwich_not_stand = PersonFactory.create(id="4322", name="Helen Hayes")
        edinburgh_candidate = PersonFactory.create(
            id="818", name="Sheila Gilmore"
        )
        edinburgh_winner = PersonFactory.create(
            id="5795", name="Tommy Sheppard"
        )
        edinburgh_may_stand = PersonFactory.create(
            id="5163", name="Peter McColl"
        )
        MembershipFactory.create(
            person=person,
            post=self.dulwich_post,
            party=self.labour_party,
            post_election=self.dulwich_post_pee,
        )
        MembershipFactory.create(
            person=person, post_election=self.edinburgh_east_post_pee
        )

        MembershipFactory.create(
            person=dulwich_not_stand,
            post=self.dulwich_post,
            party=self.labour_party,
            post_election=self.dulwich_post_pee_earlier,
        )
        dulwich_not_stand.not_standing.add(self.election)

        MembershipFactory.create(
            person=edinburgh_winner,
            post=self.edinburgh_east_post,
            party=self.labour_party,
            elected=True,
            post_election=self.edinburgh_east_post_pee,
        )

        MembershipFactory.create(
            person=edinburgh_candidate,
            post=self.edinburgh_east_post,
            party=self.labour_party,
            post_election=self.edinburgh_east_post_pee,
        )

        MembershipFactory.create(
            person=edinburgh_may_stand,
            post=self.edinburgh_east_post,
            party=self.labour_party,
            post_election=self.edinburgh_east_post_pee_earlier,
        )

    def test_api_basic_response(self):
        response = self.app.get("/api/next/")
        self.assertEqual(response.status_code, 200)
        json = response.json

        self.assertEqual(
            json["persons"], "http://localhost:80/api/next/persons/"
        )
        self.assertEqual(
            json["organizations"], "http://localhost:80/api/next/organizations/"
        )
        self.assertEqual(
            json["elections"], "http://localhost:80/api/next/elections/"
        )
        self.assertEqual(json["posts"], "http://localhost:80/api/next/posts/")

        persons_resp = self.app.get("/api/next/persons/")
        self.assertEqual(persons_resp.status_code, 200)

        organizations_resp = self.app.get("/api/next/organizations/")
        self.assertEqual(organizations_resp.status_code, 200)

        elections_resp = self.app.get("/api/next/elections/")
        self.assertEqual(elections_resp.status_code, 200)

        posts_resp = self.app.get("/api/next/posts/")
        self.assertEqual(posts_resp.status_code, 200)

        parties_resp = self.app.get("/api/next/parties/")
        self.assertEqual(parties_resp.status_code, 200)

    def test_party_endpoint(self):
        parties_resp = self.app.get("/api/next/parties/")
        self.assertEqual(parties_resp.json["count"], 6)
