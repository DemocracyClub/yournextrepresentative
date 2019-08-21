import mock

from django.test.utils import override_settings
from django_webtest import WebTest

from .auth import TestUserMixin
from .dates import mock_on_election_day_polls_closed
from .uk_examples import UK2015ExamplesMixin
from .factories import MembershipFactory
from people.tests.factories import PersonFactory


class TestWasElectedButtons(TestUserMixin, UK2015ExamplesMixin, WebTest):
    def setUp(self):
        super().setUp()
        person = PersonFactory.create(id=2009, name="Tessa Jowell")
        self.ballot = self.dulwich_post_ballot_earlier
        MembershipFactory.create(
            person=person,
            post=self.dulwich_post,
            party=self.labour_party,
            ballot=self.ballot,
        )

    def test_no_was_elected_button_before(self):
        response = self.app.get(
            self.ballot.get_absolute_url(),
            user=self.user_who_can_record_results,
        )
        self.assertNotIn(
            '<input type="submit" class="button" value="Mark candidate as elected">',
            response,
        )

    @mock.patch("django.utils.timezone.now")
    def test_show_was_elected_button_on_election_day(self, mock_now):
        mock_now.return_value = mock_on_election_day_polls_closed(
            self.ballot.election
        )
        response = self.app.get(
            self.ballot.get_absolute_url(),
            user=self.user_who_can_record_results,
        )
        self.assertContains(response, "Mark candidate as elected")

    def test_show_was_elected_button_after(self):
        response = self.app.get(
            self.ballot.get_absolute_url(),
            user=self.user_who_can_record_results,
        )
        self.assertIn("Mark candidate as elected", response)
