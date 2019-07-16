import re

from django.test.utils import override_settings
from django_webtest import WebTest

from .auth import TestUserMixin
from .dates import templates_before, templates_after
from .factories import MembershipFactory
from people.tests.factories import PersonFactory
from people.models import PersonImage
from .uk_examples import UK2015ExamplesMixin
from candidates.tests.helpers import TmpMediaRootMixin
from moderation_queue.tests.paths import EXAMPLE_IMAGE_FILENAME


class PersonViewSharedTestsMixin(
    TmpMediaRootMixin, TestUserMixin, UK2015ExamplesMixin, WebTest
):
    maxDiff = None

    def setUp(self):
        super().setUp()
        self.person = PersonFactory.create(id=2009, name="Tessa Jowell")
        MembershipFactory.create(
            person=self.person,
            post=self.dulwich_post,
            party=self.labour_party,
            ballot=self.dulwich_post_ballot,
        )

    def test_get_tessa_jowell(self):
        response = self.app.get("/person/2009/tessa-jowell")
        self.assertTrue(
            re.search(
                """<h1>Tessa Jowell</h1>\s+
        <p>
          Candidate for <a href="/elections/parl.65808.2015-05-07/">Dulwich and West Norwood</a> in <a href="/elections/parl.2015-05-07/">2015 General Election</a>
        </p>
""",
                response.text,
                re.MULTILINE | re.IGNORECASE,
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

    def test_photo_credits_shown(self):
        PersonImage.objects.create_from_file(
            EXAMPLE_IMAGE_FILENAME,
            "images/jowell-pilot.jpg",
            defaults={
                "person": self.person,
                "is_primary": True,
                "source": "Taken from Wikipedia",
                "copyright": "example-license",
                "uploading_user": self.user,
                "user_notes": "A photo of Tessa Jowell",
            },
        )
        req = self.app.get(self.person.get_absolute_url())
        self.assertContains(req, "Photo Credit:")
        self.assertContains(req, "Taken from Wikipedia")
