import mock
from django.urls import reverse
from django_webtest import WebTest
from people.models import Person
from people.tests.factories import PersonFactory
from results.models import ResultEvent

from .auth import TestUserMixin
from .dates import mock_in_past
from .factories import MembershipFactory
from .uk_examples import UK2015ExamplesMixin


class TestRecordWinner(TestUserMixin, UK2015ExamplesMixin, WebTest):
    def setUp(self):
        super().setUp()
        self.ballot = self.dulwich_post_ballot_earlier
        person = PersonFactory.create(id=2009, name="Tessa Jowell")
        MembershipFactory.create(
            person=person,
            post=self.dulwich_post,
            party=self.labour_party,
            ballot=self.ballot,
        )

        self.winner = PersonFactory.create(id=4322, name="Helen Hayes")

        MembershipFactory.create(
            person=self.winner,
            post=self.dulwich_post,
            party=self.labour_party,
            ballot=self.dulwich_post_ballot_earlier,
        )

    @mock.patch("django.utils.timezone.now")
    def test_record_winner_link_present(self, mock_now):
        mock_now.return_value = mock_in_past()
        self.assertTrue(self.dulwich_post_ballot_earlier.polls_closed)
        response = self.app.get(
            self.dulwich_post_ballot_earlier.get_absolute_url(),
            user=self.user_who_can_record_results,
        )
        self.assertContains(response, "Mark candidate as elected")
        record_url = reverse(
            "record-winner",
            kwargs={"ballot_paper_id": self.ballot.ballot_paper_id},
        )
        self.assertContains(response, record_url)

    def test_record_winner_link_not_present(self):
        response = self.app.get(
            self.dulwich_post_ballot.get_absolute_url(), user=self.user
        )
        self.assertNotIn("Mark candidate as elected", response.text)

    def test_record_winner_not_privileged(self):
        # Get the constituency page just to set the CSRF token
        self.app.get(
            self.dulwich_post_ballot.get_absolute_url(), user=self.user
        )
        csrftoken = self.app.cookies["csrftoken"]

        base_record_url = reverse(
            "record-winner",
            kwargs={
                "ballot_paper_id": self.dulwich_post_ballot.ballot_paper_id
            },
        )
        form_get_response = self.app.post(
            base_record_url, {"person_id": 4322}, expect_errors=True
        )
        self.assertEqual(form_get_response.status_code, 403)
        post_response = self.app.post(
            base_record_url,
            params={
                "csrfmiddlewaretoken": csrftoken,
                "person_id": "4322",
                "source": "BBC news",
            },
            expect_errors=True,
        )
        self.assertEqual(post_response.status_code, 403)
        self.assertEqual(0, ResultEvent.objects.count())

    def test_record_winner_privileged(self):
        self._get_winner_button_form(self.ballot, 4322).submit()

        person = Person.objects.get(id=4322)
        self.assertTrue(person.get_elected(self.ballot.election))
        resultevent = ResultEvent.objects.get()
        self.assertEqual(resultevent.election, self.ballot.election)
        self.assertEqual(resultevent.winner, self.winner)
        self.assertEqual(resultevent.old_post_id, "65808")
        self.assertEqual(
            resultevent.old_post_name,
            "Member of Parliament for Dulwich and West Norwood",
        )
        self.assertEqual(resultevent.post, self.ballot.post)
        self.assertEqual(resultevent.winner_party, self.labour_party)
        self.assertEqual(
            resultevent.source, "[Quick update from the constituency page]"
        )
        self.assertEqual(resultevent.user, self.user_who_can_record_results)
        self.assertEqual(resultevent.parlparse_id, "")
        self.assertEqual(resultevent.retraction, False)

    def _get_winner_button_form(self, ballot, person_id, user=None):
        if not user:
            user = self.user_who_can_record_results
        form_id = "winner-confirm_{}".format(person_id)
        req = self.app.get(self.ballot.get_absolute_url(), user=user)
        return req.forms[form_id]

    def test_cannot_record_multiple_winners(self):
        self.assertEqual(
            self.ballot.membership_set.filter(elected=True).count(), 0
        )

        form1 = self._get_winner_button_form(self.ballot, self.winner.pk)
        form2 = self._get_winner_button_form(self.ballot, 2009)
        form1.submit()
        form2_resp = form2.submit()
        self.assertEqual(
            self.ballot.membership_set.filter(elected=True).count(), 1
        )
        self.assertEqual(
            self.ballot.membership_set.get(elected=True).person, self.winner
        )

        self.assertEqual(form2_resp.status_code, 200)
        self.assertContains(form2_resp, "Winner already set for")
        self.assertEqual(form2_resp.context["winner_logged_action"].count(), 1)

    def test_record_multiple_winners(self):
        self.ballot.election.people_elected_per_post = 2
        self.ballot.election.save()
        self.ballot.winner_count = 2
        self.ballot.save()

        self._get_winner_button_form(self.ballot, "4322").submit()
        self._get_winner_button_form(self.ballot, "2009").submit()

        person = Person.objects.get(id=2009)
        self.assertTrue(person.get_elected(self.ballot.election))
        self.assertEqual(2, ResultEvent.objects.count())
        self.assertEqual(
            2, ResultEvent.objects.filter(retraction=False).count()
        )


class TestRetractWinner(TestUserMixin, UK2015ExamplesMixin, WebTest):
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

        self.winner = PersonFactory.create(id=4322, name="Helen Hayes")

        MembershipFactory.create(
            person=self.winner,
            post=self.ballot.post,
            party=self.labour_party,
            elected=True,
            ballot=self.ballot,
        )

    def test_retract_winner_link_present(self):
        response = self.app.get(
            self.ballot.get_absolute_url(),
            user=self.user_who_can_record_results,
        )
        self.assertContains(response, "Unset the current winners")
        record_url = reverse(
            "retract-winner",
            kwargs={"ballot_paper_id": self.ballot.ballot_paper_id},
        )
        self.assertContains(response, record_url)

    def test_retract_winner_link_not_present(self):
        response = self.app.get(self.ballot.get_absolute_url(), user=self.user)
        self.assertNotIn("Unset the current winners", response.text)

    def test_retract_winner_not_privileged(self):
        # Get the constituency page just to set the CSRF token
        self.app.get(self.ballot.get_absolute_url(), user=self.user)
        csrftoken = self.app.cookies["csrftoken"]
        base_record_url = reverse(
            "retract-winner",
            kwargs={"ballot_paper_id": self.ballot.ballot_paper_id},
        )
        form_get_response = self.app.get(
            base_record_url + "?person=4322", expect_errors=True
        )
        self.assertEqual(form_get_response.status_code, 403)
        post_response = self.app.post(
            base_record_url,
            params={
                "csrfmiddlewaretoken": csrftoken,
                "person_id": "4322",
                "source": "BBC news",
            },
            expect_errors=True,
        )
        self.assertEqual(post_response.status_code, 403)
        self.assertEqual(0, ResultEvent.objects.count())

    def test_retract_winner_privileged(self):
        self.app.get(
            self.ballot.get_absolute_url(),
            user=self.user_who_can_record_results,
        )
        csrftoken = self.app.cookies["csrftoken"]
        base_record_url = reverse(
            "retract-winner",
            kwargs={"ballot_paper_id": self.ballot.ballot_paper_id},
        )
        response = self.app.post(
            base_record_url,
            params={"csrfmiddlewaretoken": csrftoken},
            user=self.user_who_can_record_results,
            expect_errors=True,
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.location, self.ballot.get_absolute_url())

        person = Person.objects.get(id=4322)
        self.assertFalse(person.get_elected(self.ballot.election))

        self.assertEqual(1, ResultEvent.objects.count())
        resultevent = ResultEvent.objects.get()
        self.assertEqual(resultevent.election, self.ballot.election)
        self.assertEqual(resultevent.winner, self.winner)
        self.assertEqual(resultevent.old_post_id, "65808")
        self.assertEqual(
            resultevent.old_post_name,
            "Member of Parliament for Dulwich and West Norwood",
        )
        self.assertEqual(resultevent.post, self.ballot.post)
        self.assertEqual(resultevent.winner_party, self.labour_party)
        self.assertEqual(
            resultevent.source, "Result recorded in error, retracting"
        )
        self.assertEqual(resultevent.user, self.user_who_can_record_results)
        self.assertEqual(resultevent.parlparse_id, "")
        self.assertEqual(resultevent.retraction, True)
