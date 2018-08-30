import re
from django_webtest import WebTest

from popolo.models import Membership

from .auth import TestUserMixin
from .factories import MembershipFactory, MembershipFactory, PersonFactory
from .uk_examples import UK2015ExamplesMixin


class TestConstituenciesDeclared(TestUserMixin, UK2015ExamplesMixin, WebTest):
    def setUp(self):
        super().setUp()

        tessa_jowell = PersonFactory.create(id="2009", name="Tessa Jowell")
        MembershipFactory.create(
            person=tessa_jowell,
            post=self.dulwich_post,
            on_behalf_of=self.labour_party_extra.base,
            post_election=self.dulwich_post_pee,
        )

        winner = PersonFactory.create(id="4322", name="Helen Hayes")
        MembershipFactory.create(
            person=winner,
            post=self.dulwich_post,
            on_behalf_of=self.labour_party_extra.base,
            elected=True,
            post_election=self.dulwich_post_pee,
        )

        james_smith = PersonFactory.create(id="2010", name="James Smith")
        MembershipFactory.create(
            person=james_smith,
            post=self.camberwell_post,
            on_behalf_of=self.labour_party_extra.base,
            post_election=self.camberwell_post_pee,
        )

    def test_constituencies_declared(self):
        response = self.app.get("/election/2015/constituencies/declared")

        self.assertEqual(response.status_code, 200)
        response.mustcontain("Dulwich")
        response.mustcontain("Camberwell")

        response.mustcontain("3 still undeclared (25% done)")

    def test_constituencies_declared_bad_election(self):
        response = self.app.get(
            "/election/2014/constituencies/declared", expect_errors=True
        )

        self.assertEqual(response.status_code, 404)

    def test_constituencies_appear_when_declared(self):
        response = self.app.get("/election/2015/constituencies/declared")

        self.assertEqual(response.status_code, 200)
        self.assertTrue(
            re.search(
                r"""(?ms)<del><a[^>]*>Member of Parliament for Dulwich and West Norwood""",
                response.text,
            )
        )
        self.assertTrue(
            re.search(
                r"""(?ms)<a[^>]*>Member of Parliament for Camberwell and Peckham""",
                response.text,
            )
        )
        self.assertFalse(
            re.search(
                r"""(?ms)<del><a[^>]*>Member of Parliament for Camberwell and Peckham""",
                response.text,
            )
        )
        response.mustcontain("3 still undeclared (25% done)")

        unelected = Membership.objects.filter(
            post_election__election=self.election,
            person_id=2010,
            post__slug="65913",
        ).first()

        unelected.elected = True
        unelected.save()

        response = self.app.get("/election/2015/constituencies/declared")

        self.assertEqual(response.status_code, 200)
        self.assertTrue(
            re.search(
                r"""(?ms)<del><a[^>]*>Member of Parliament for Dulwich and West Norwood""",
                response.text,
            )
        )
        self.assertTrue(
            re.search(
                r"""(?ms)<del><a[^>]*>Member of Parliament for Camberwell and Peckham""",
                response.text,
            )
        )
        response.mustcontain("2 still undeclared (50% done)")
