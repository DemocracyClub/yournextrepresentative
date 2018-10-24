from django_webtest import WebTest

from .auth import TestUserMixin

from .factories import MembershipFactory, PersonFactory, PostFactory
from .uk_examples import UK2015ExamplesMixin


class TestAreasOfTypeView(TestUserMixin, UK2015ExamplesMixin, WebTest):
    def setUpAll(self):
        super().setUp()
        person = PersonFactory.create(id=2009, name="Tessa Jowell")
        MembershipFactory.create(
            person=person,
            post=self.dulwich_post,
            party=self.labour_party,
            post_election=self.dulwich_post_pee,
        )

        PostFactory.create(
            elections=(self.election,),
            organization=self.commons,
            slug="65730",
            label="Member of Parliament for Aldershot",
            party_set=self.gb_parties,
        )

    def test_any_areas_of_type_page_without_login(self):
        response = self.app.get("/areas-of-type/WMC/")
        self.assertEqual(response.status_code, 301)

    def test_get_malformed_url(self):
        response = self.app.get(
            "/areas-of-type/3243452345/invalid", expect_errors=True
        )
        self.assertEqual(response.status_code, 301)

    def test_get_non_existent(self):
        response = self.app.get("/areas-of-type/AAA/", expect_errors=True)
        self.assertEqual(response.status_code, 301)

    def test_posts_of_type(self):
        response = self.app.get("/posts-of-type/WMC/", expect_errors=True)
        self.assertEqual(response.status_code, 200)
