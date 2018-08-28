import re
from django_webtest import WebTest

from .auth import TestUserMixin
from .factories import MembershipFactory, MembershipFactory, PersonFactory
from .uk_examples import UK2015ExamplesMixin


class TestRecordWinner(TestUserMixin, UK2015ExamplesMixin, WebTest):
    def setUp(self):
        super().setUp()

        tessa_jowell = PersonFactory.create(id="2009", name="Tessa Jowell")
        MembershipFactory.create(
            person=tessa_jowell,
            post=self.dulwich_post,
            on_behalf_of=self.labour_party_extra.base,
            party_list_position=1,
            post_election=self.dulwich_post_pee,
        )

        winner = PersonFactory.create(id="4322", name="Helen Hayes")
        MembershipFactory.create(
            person=winner,
            post=self.dulwich_post,
            on_behalf_of=self.labour_party_extra.base,
            party_list_position=2,
            post_election=self.dulwich_post_pee,
        )

        james_smith = PersonFactory.create(id="2010", name="James Smith")
        MembershipFactory.create(
            person=james_smith,
            post=self.dulwich_post,
            on_behalf_of=self.labour_party_extra.base,
            party_list_position=3,
            post_election=self.dulwich_post_pee,
        )

    def test_party_list_page(self):
        response = self.app.get(
            "/election/2015/party-list/65808/" + self.labour_party_extra.slug
        )

        self.assertEqual(response.status_code, 200)
        response.mustcontain("Tessa Jowell")
        response.mustcontain("Helen Hayes")
        response.mustcontain("James Smith")

        self.assertTrue(
            re.search(
                r"""(?ms)1</span>\s*<img[^>]*>\s*<div class="person-name-and-party">\s*<a[^>]*>Tessa Jowell""",
                response.text,
            )
        )

    def test_bad_party_returns_404(self):
        response = self.app.get(
            "/election/2015/party-list/65808/asdjfhsdkfj", expect_errors=True
        )

        self.assertEqual(response.status_code, 404)

    def test_no_ordering_on_constituency_page(self):
        response = self.app.get(
            "/election/2015/post/65808/dulwich_and_west_norwood"
        )

        self.assertEqual(response.status_code, 200)
        response.mustcontain("Tessa Jowell")
        response.mustcontain("Helen Hayes")
        response.mustcontain("James Smith")

        self.assertFalse(
            re.search(
                r"""(?ms)1\s*<img[^>]*>\s*<div class="person-name-and-party">\s*<a[^>]*>Tessa Jowell""",
                response.text,
            )
        )

    def test_links_to_party_list_if_list_length(self):
        self.election.party_lists_in_use = True
        self.election.default_party_list_members_to_show = 2
        self.election.save()

        response = self.app.get(
            "/election/2015/post/65808/dulwich_and_west_norwood"
        )

        self.assertEqual(response.status_code, 200)
        response.mustcontain("Tessa Jowell")
        response.mustcontain("Helen Hayes")
        response.mustcontain(no="James Smith")

        response.mustcontain(
            '<a href="/election/2015/party-list/65808/{}">See all 3 members on the party list'.format(
                self.labour_party_extra.slug
            )
        )

        self.assertFalse(
            re.search(
                r"""(?ms)1\s*<img[^>]*>\s*<div class="person-name-and-party">\s*<a[^>]*>Tessa Jowell""",
                response.text,
            )
        )
