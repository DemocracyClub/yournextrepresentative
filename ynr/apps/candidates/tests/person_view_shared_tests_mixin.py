import re

from django.test.utils import override_settings
from django_webtest import WebTest

from .auth import TestUserMixin
from .dates import templates_before, templates_after
from .factories import MembershipFactory
from people.tests.factories import PersonFactory
from .uk_examples import UK2015ExamplesMixin


class PersonViewSharedTestsMixin(TestUserMixin, UK2015ExamplesMixin, WebTest):
    def setUp(self):
        super().setUp()
        person = PersonFactory.create(id=2009, name="Tessa Jowell")
        MembershipFactory.create(
            person=person,
            post=self.dulwich_post,
            party=self.labour_party,
            post_election=self.dulwich_post_pee,
        )

    def test_get_tessa_jowell(self):
        response = self.app.get("/person/2009/tessa-jowell")
        self.assertTrue(
            re.search(
                r"""(?msx)
  <h1>Tessa\s+Jowell</h1>\s*
  <p>Candidate\s+for\s+
  <a\s+href="/election/2015/post/65808/dulwich-and-west-norwood">Dulwich\s+
  and\s+West\s+Norwood</a>\s+in\ <a\ href="/election/2015/constituencies">2015
  \s+General\s+Election</a>\s*</p>""",
                response.text,
            )
        )

    @override_settings(TEMPLATES=templates_before)
    def test_get_tessa_jowell_before_election(self):
        response = self.app.get("/person/2009/tessa-jowell")
        self.assertContains(response, "Contesting the 2015 General Election")

    @override_settings(TEMPLATES=templates_after)
    def test_get_tessa_jowell_after_election(self):
        response = self.app.get("/person/2009/tessa-jowell")
        self.assertContains(response, "Contested the 2015 General Election")

    def test_get_non_existent(self):
        response = self.app.get(
            "/person/987654/imaginary-person", expect_errors=True
        )
        self.assertEqual(response.status_code, 404)

    def test_shows_no_edit_buttons_if_user_not_authenticated(self):
        response = self.app.get("/person/2009/tessa-jowell")
        edit_buttons = response.html.find_all("a", attrs={"class": "button"})
        self.assertEqual(len(edit_buttons), 2)
        self.assertEqual(edit_buttons[0].string, "Log in to edit")

    def test_shows_edit_buttons_if_user_authenticated(self):
        response = self.app.get("/person/2009/tessa-jowell", user=self.user)
        edit_buttons = response.html.find_all("a", attrs={"class": "button"})
        self.assertEqual(len(edit_buttons), 3)

    def test_links_to_person_edit_page(self):
        response = self.app.get("/person/2009/tessa-jowell", user=self.user)
        self.assertContains(response, 'href="/person/2009/update"')

    def test_links_to_person_photo_upload_page(self):
        response = self.app.get("/person/2009/tessa-jowell", user=self.user)
        self.assertContains(response, 'href="/moderation/photo/upload/2009"')
