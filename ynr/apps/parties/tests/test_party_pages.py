from candidates.tests.factories import MembershipFactory, PostFactory
from candidates.tests.uk_examples import UK2015ExamplesMixin
from django_webtest import WebTest
from people.models import PersonIdentifier
from people.tests.factories import PersonFactory


class TestPartyPages(UK2015ExamplesMixin, WebTest):
    def setUp(self):
        super().setUp()
        constituencies = {}
        for slug, cons_name, country in [
            ("66090", "Cardiff Central", "Wales"),
            ("65672", "Doncaster North", "England"),
            ("65719", "South Shields", "England"),
        ]:
            constituencies[cons_name] = PostFactory.create(
                elections=(self.election, self.earlier_election),
                organization=self.commons,
                slug=slug,
                label="Member of Parliament for {}".format(cons_name),
                group=country,
            )

        person = PersonFactory.create(id=3056, name="Ed Miliband")
        MembershipFactory.create(
            person=person,
            post=constituencies["Doncaster North"],
            party=self.labour_party,
            ballot=self.election.ballot_set.get(
                post=constituencies["Doncaster North"]
            ),
        )
        person = PersonFactory.create(id=3814, name="David Miliband")
        MembershipFactory.create(
            person=person,
            post=constituencies["South Shields"],
            party=self.labour_party,
            ballot=self.earlier_election.ballot_set.get(
                post=constituencies["South Shields"]
            ),
        )
        conservative_opponent = PersonFactory.create(
            id="6648", name="Mark Fletcher"
        )
        MembershipFactory.create(
            person=conservative_opponent,
            post=constituencies["South Shields"],
            party=self.conservative_party,
            ballot=self.election.ballot_set.get(
                post=constituencies["South Shields"]
            ),
        )

    def test_single_party_page(self):
        response = self.app.get("/parties/PP53/elections/parl.2015-05-07/")

        self.assertEqual(
            response.context["candidates"][0].person.name, "Ed Miliband"
        )

        self.assertEqual(response.context["candidates"].count(), 1)

    def test_single_party_page_shows_person_identifiers(self):
        response = self.app.get("/parties/PP53/elections/parl.2015-05-07/")

        self.assertNotContains(response, "Ed_Miliband")
        self.assertNotContains(response, "ed@miliband.com")
        PersonIdentifier.objects.create(
            value_type="twitter_username", value="Ed_Miliband", person_id="3056"
        )
        PersonIdentifier.objects.create(
            value_type="email", value="ed@miliband.com", person_id="3056"
        )
        response = self.app.get("/parties/PP53/elections/parl.2015-05-07/")
        self.assertContains(response, "Ed_Miliband")
        self.assertContains(response, "ed@miliband.com")

    def test_single_party_page_no_candidates(self):
        response = self.app.get("/parties/PP63/elections/parl.2015-05-07/")
        self.assertFalse(response.context["candidates"].exists())
        self.assertContains(
            response,
            "We don't know of any Green Party candidates in the 2015 General Election so far.",
        )
