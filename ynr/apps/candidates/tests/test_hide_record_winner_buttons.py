from django.test.utils import override_settings
from django_webtest import WebTest

from .auth import TestUserMixin
from .dates import templates_before, templates_on_election_day, templates_after
from .uk_examples import UK2015ExamplesMixin
from .factories import MembershipFactory, PersonFactory


class TestWasElectedButtons(TestUserMixin, UK2015ExamplesMixin, WebTest):
    def setUp(self):
        super().setUp()
        person = PersonFactory.create(id=2009, name="Tessa Jowell")
        MembershipFactory.create(
            person=person,
            post=self.dulwich_post,
            party=self.labour_party,
            post_election=self.dulwich_post_pee,
        )

    @override_settings(TEMPLATES=templates_before)
    def test_no_was_elected_button_before(self):
        response = self.app.get(
            "/election/2015/post/65808/dulwich-and-west-norwood",
            user=self.user_who_can_record_results,
        )
        self.assertNotIn(
            '<input type="submit" class="button" value="Mark candidate as elected">',
            response,
        )

    @override_settings(TEMPLATES=templates_on_election_day)
    def test_show_was_elected_button_on_election_day(self):
        response = self.app.get(
            "/election/2015/post/65808/dulwich-and-west-norwood",
            user=self.user_who_can_record_results,
        )
        self.assertIn(
            '<input type="submit" class="button" value="Mark candidate as elected">',
            response,
        )

    @override_settings(TEMPLATES=templates_after)
    def test_show_was_elected_button_after(self):
        response = self.app.get(
            "/election/2015/post/65808/dulwich-and-west-norwood",
            user=self.user_who_can_record_results,
        )
        self.assertIn(
            '<input type="submit" class="button" value="Mark candidate as elected">',
            response,
        )
