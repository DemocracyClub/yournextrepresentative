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
            kwargs={
                "election": self.ballot.election.slug,
                "post_id": self.ballot.post.slug,
            },
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
            kwargs={"election": "parl.2015-05-07", "post_id": "65808"},
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

    def test_record_winner_privileged(self):
        base_record_url = reverse(
            "record-winner",
            kwargs={
                "election": self.ballot.election.slug,
                "post_id": self.ballot.post.slug,
            },
        )
        form_get_response = self.app.get(
            base_record_url + "?person=4322",
            user=self.user_who_can_record_results,
            expect_errors=True,
        )
        form = form_get_response.forms["record_winner"]
        self.assertEqual(form_get_response.status_code, 200)
        form["source"] = "BBC website"
        submission_response = form.submit()
        self.assertEqual(submission_response.status_code, 302)
        self.assertEqual(
            submission_response.location, self.ballot.get_absolute_url()
        )

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
        self.assertEqual(resultevent.source, "BBC website")
        self.assertEqual(resultevent.user, self.user_who_can_record_results)
        self.assertEqual(resultevent.parlparse_id, "")
        self.assertEqual(resultevent.retraction, False)

    def test_cannot_record_multiple_winners(self):
        base_record_url = reverse(
            "record-winner",
            kwargs={
                "election": self.ballot.election.slug,
                "post_id": self.ballot.post.slug,
            },
        )
        form_get_response = self.app.get(
            base_record_url + "?person=4322",
            user=self.user_who_can_record_results,
            expect_errors=True,
        )
        form = form_get_response.forms["record_winner"]
        self.assertEqual(form_get_response.status_code, 200)
        form["source"] = "BBC website"
        submission_response = form.submit()
        self.assertEqual(submission_response.status_code, 302)
        self.assertEqual(
            submission_response.location, self.ballot.get_absolute_url()
        )

        person = Person.objects.get(id=4322)
        self.assertTrue(person.get_elected(self.ballot.election))

        form_get_response = self.app.get(
            base_record_url + "?person=2009",
            user=self.user_who_can_record_results,
            expect_errors=True,
        )
        self.assertEqual(form_get_response.status_code, 200)
        form["source"] = "BBC website"
        with self.assertRaises(Exception) as context:
            submission_response = form.submit()
            self.assertEqual(
                "There were already 1 winners" in context.exception
            )
        self.assertEqual(1, ResultEvent.objects.count())
        self.assertFalse(ResultEvent.objects.get().retraction)

    def test_record_multiple_winners(self):
        self.ballot.election.people_elected_per_post = 2
        self.ballot.election.save()
        self.ballot.winner_count = 2
        self.ballot.save()

        base_record_url = reverse(
            "record-winner",
            kwargs={
                "election": self.ballot.election.slug,
                "post_id": self.ballot.post.slug,
            },
        )
        form_get_response = self.app.get(
            base_record_url + "?person=4322",
            user=self.user_who_can_record_results,
            expect_errors=True,
        )
        form = form_get_response.forms["record_winner"]
        self.assertEqual(form_get_response.status_code, 200)
        form["source"] = "BBC website"
        submission_response = form.submit()
        self.assertEqual(submission_response.status_code, 302)
        self.assertEqual(
            submission_response.location, self.ballot.get_absolute_url()
        )

        person = Person.objects.get(id=4322)
        self.assertTrue(person.get_elected(self.ballot.election))

        form_get_response = self.app.get(
            base_record_url + "?person=2009",
            user=self.user_who_can_record_results,
            expect_errors=True,
        )
        form = form_get_response.forms["record_winner"]
        self.assertEqual(form_get_response.status_code, 200)
        form["source"] = "BBC website"
        submission_response = form.submit()
        self.assertEqual(submission_response.status_code, 302)
        self.assertEqual(
            submission_response.location, self.ballot.get_absolute_url()
        )

        person = Person.objects.get(id=2009)
        self.assertTrue(person.get_elected(self.ballot.election))
        self.assertEqual(2, ResultEvent.objects.count())
        self.assertEqual(
            2, ResultEvent.objects.filter(retraction=False).count()
        )

    def test_record_multiple_winners_per_post_setting(self):

        self.ballot.winner_count = 2
        self.ballot.save()
        base_record_url = reverse(
            "record-winner",
            kwargs={
                "election": self.ballot.election.slug,
                "post_id": self.ballot.post.slug,
            },
        )
        form_get_response = self.app.get(
            base_record_url + "?person=4322",
            user=self.user_who_can_record_results,
            expect_errors=True,
        )
        form = form_get_response.forms["record_winner"]
        self.assertEqual(form_get_response.status_code, 200)
        form["source"] = "BBC website"
        submission_response = form.submit()
        self.assertEqual(submission_response.status_code, 302)
        self.assertEqual(
            submission_response.location, self.ballot.get_absolute_url()
        )

        person = Person.objects.get(id=4322)
        self.assertTrue(person.get_elected(self.ballot.election))

        form_get_response = self.app.get(
            base_record_url + "?person=2009",
            user=self.user_who_can_record_results,
            expect_errors=True,
        )
        form = form_get_response.forms["record_winner"]
        self.assertEqual(form_get_response.status_code, 200)
        form["source"] = "BBC website"
        submission_response = form.submit()
        self.assertEqual(submission_response.status_code, 302)
        self.assertEqual(
            submission_response.location, self.ballot.get_absolute_url()
        )

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
            kwargs={
                "election": self.ballot.election.slug,
                "post_id": self.ballot.post.slug,
            },
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
            kwargs={
                "election": self.ballot.election.slug,
                "post_id": self.ballot.post.slug,
            },
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
            kwargs={
                "election": self.ballot.election.slug,
                "post_id": self.ballot.post.slug,
            },
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
