from django.urls import reverse
from django_webtest import WebTest

from bulk_adding.models import RawPeople
from candidates.models import Ballot
from candidates.tests.auth import TestUserMixin
from candidates.tests.factories import MembershipFactory
from candidates.tests.uk_examples import UK2015ExamplesMixin
from parties.tests.factories import PartyFactory
from people.models import Person
from people.tests.factories import PersonFactory
from popolo.models import Post


def update_lock(post, election, lock_status):
    ballot = post.ballot_set.get(election=election)
    ballot.candidates_locked = lock_status
    ballot.save()

    return ballot


class TestConstituencyLockAndUnlock(
    TestUserMixin, UK2015ExamplesMixin, WebTest
):
    def setUp(self):
        super().setUp()
        update_lock(self.camberwell_post, self.election, True)
        self.post_id = self.dulwich_post.id

    def test_constituency_lock_unauthorized(self):
        self.app.get(
            self.dulwich_post_ballot.get_absolute_url(), user=self.user
        )
        csrftoken = self.app.cookies["csrftoken"]
        response = self.app.post(
            "/election/2015/lock/",
            params={
                "lock": "True",
                "post_id": "65808",
                "csrfmiddlewaretoken": csrftoken,
            },
            user=self.user,
            expect_errors=True,
        )
        self.assertEqual(response.status_code, 403)

    def test_constituency_lock_bad_submission(self):
        post = Post.objects.get(id=self.post_id)
        update_lock(post, self.election, False)
        self.app.get(
            self.dulwich_post_ballot.get_absolute_url(),
            user=self.user_who_can_lock,
        )
        csrftoken = self.app.cookies["csrftoken"]
        with self.assertRaises(Exception) as context:
            self.app.post(
                "/election/2015/lock/",
                params={"csrfmiddlewaretoken": csrftoken},
                user=self.user_who_can_lock,
                expect_errors=True,
            )

            self.assertTrue("Invalid data POSTed" in context.exception)

    def test_constituency_lock(self):
        post = Post.objects.get(id=self.post_id)
        ballot = update_lock(post, self.election, False)
        self.assertEqual(False, ballot.candidates_locked)

        # Create a RawInput model
        RawPeople.objects.create(ballot=ballot, data={})

        self.app.get(
            self.dulwich_post_ballot.get_absolute_url(),
            user=self.user_who_can_lock,
        )
        csrftoken = self.app.cookies["csrftoken"]
        response = self.app.post(
            reverse(
                "constituency-lock",
                kwargs={"ballot_id": ballot.ballot_paper_id},
            ),
            params={"csrfmiddlewaretoken": csrftoken},
            user=self.user_who_can_lock,
            expect_errors=False,
        )

        ballot = Ballot.objects.get(ballot_paper_id="parl.65808.2015-05-07")

        self.assertEqual(True, ballot.candidates_locked)
        self.assertFalse(RawPeople.objects.exists())
        self.assertFalse(hasattr(ballot, "rawpeople"))
        self.assertEqual(response.status_code, 302)
        self.assertEqual(
            response.location, self.dulwich_post_ballot.get_absolute_url()
        )

    def test_constituency_unlock(self):
        MembershipFactory(
            ballot=self.dulwich_post_ballot,
            person=PersonFactory(),
            party=PartyFactory(),
        )
        ballot = self.dulwich_post_ballot
        ballot.candidates_locked = True
        ballot.save()
        response = self.app.get(
            self.dulwich_post_ballot.get_absolute_url(),
            user=self.user_who_can_lock,
        )
        csrftoken = self.app.cookies["csrftoken"]
        self.assertContains(response, "Unlock candidate list")
        response = self.app.post(
            reverse(
                "constituency-lock",
                kwargs={"ballot_id": ballot.ballot_paper_id},
            ),
            params={"csrfmiddlewaretoken": csrftoken},
            user=self.user_who_can_lock,
        )
        ballot.refresh_from_db()
        self.assertFalse(ballot.candidates_locked)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(
            response.location, self.dulwich_post_ballot.get_absolute_url()
        )

    def test_constituencies_unlocked_list(self):
        response = self.app.get("/elections/parl.2015-05-07/unlocked/")
        self.assertEqual(response.status_code, 200)
        self.assertIn("Dulwich", response.text)
        self.assertNotIn("Camberwell", response.text)


class TestConstituencyLockWorks(TestUserMixin, UK2015ExamplesMixin, WebTest):
    def setUp(self):
        super().setUp()
        update_lock(self.camberwell_post, self.election, True)
        post_locked = self.camberwell_post
        self.post_id = self.dulwich_post.id
        person = PersonFactory.create(id=4170, name="Naomi Newstead")

        MembershipFactory.create(
            person=person,
            post=post_locked,
            party=self.green_party,
            ballot=post_locked.ballot_set.get(election=self.election),
        )

        person = PersonFactory.create(id=4322, name="Helen Hayes")

        MembershipFactory.create(
            person=person,
            post=self.dulwich_post,
            party=self.green_party,
            ballot=self.dulwich_post.ballot_set.get(election=self.election),
        )

    def test_add_when_locked_unprivileged_disallowed(self):
        # Just get that page for the csrftoken cookie; the form won't
        # appear on the page, since the constituency is locked:
        response = self.app.get(
            self.camberwell_post_ballot.get_absolute_url(), user=self.user
        )
        csrftoken = self.app.cookies["csrftoken"]
        response = self.app.post(
            "/election/parl.2015-05-07/person/create/",
            params={
                "tmp_person_identifiers-TOTAL_FORMS": "2",
                "tmp_person_identifiers-INITIAL_FORMS": "0",
                "tmp_person_identifiers-MIN_NUM_FORMS": "0",
                "tmp_person_identifiers-MAX_NUM_FORMS": "1000",
                "csrfmiddlewaretoken": csrftoken,
                "name": "Imaginary Candidate",
                "party_GB_parl.2015-05-07": self.green_party.ec_id,
                "constituency_parl.2015-05-07": "65913",
                "standing_parl.2015-05-07": "standing",
                "source": "Testing adding a new candidate to a locked constituency",
            },
            expect_errors=True,
        )
        self.assertEqual(response.status_code, 403)

    def test_add_when_locked_privileged_allowed(self):
        self.camberwell_post_ballot.candidates_locked = False
        self.camberwell_post_ballot.save()
        response = self.app.get(
            self.camberwell_post_ballot.get_absolute_url(),
            user=self.user_who_can_lock,
        )

        form = response.forms["new-candidate-form"]
        form["name"] = "Imaginary Candidate"
        form["party_GB_parl.2015-05-07"] = self.green_party.ec_id
        form[
            "source"
        ] = "Testing adding a new candidate to a locked constituency"
        submission_response = form.submit()
        self.assertEqual(submission_response.status_code, 302)
        # Find the person this should have redirected to:
        expected_person = Person.objects.get(name="Imaginary Candidate")
        self.assertEqual(
            submission_response.location,
            "/person/{}".format(expected_person.id),
        )

    def test_move_into_locked_unprivileged_disallowed(self):
        response = self.app.get("/person/4322/update", user=self.user)
        form = response.forms["person-details"]
        form["source"] = "Testing a switch to a locked constituency"
        form["constituency_parl.2015-05-07"] = "65913"
        submission_response = form.submit(expect_errors=True)
        self.assertEqual(submission_response.status_code, 403)

    def test_move_into_locked_privileged_allowed(self):
        response = self.app.get(
            "/person/4322/update", user=self.user_who_can_lock
        )
        form = response.forms["person-details"]
        form["source"] = "Testing a switch to a locked constituency"
        form["constituency_parl.2015-05-07"] = "65913"
        submission_response = form.submit()
        self.assertEqual(submission_response.status_code, 302)
        self.assertEqual(submission_response.location, "/person/4322")

    def test_move_out_of_locked_unprivileged_disallowed(self):
        response = self.app.get("/person/4170/update", user=self.user)
        form = response.forms["person-details"]
        form["source"] = "Testing a switch to a unlocked constituency"
        form["constituency_parl.2015-05-07"] = "65808"
        submission_response = form.submit(expect_errors=True)
        self.assertEqual(submission_response.status_code, 403)

    def test_move_out_of_locked_privileged_allowed(self):
        response = self.app.get(
            "/person/4170/update", user=self.user_who_can_lock
        )
        form = response.forms["person-details"]
        form["source"] = "Testing a switch to a unlocked constituency"
        form["constituency_parl.2015-05-07"] = "65808"
        submission_response = form.submit()
        self.assertEqual(submission_response.status_code, 302)
        self.assertEqual(submission_response.location, "/person/4170")

    # Now the tests to check that the only privileged users can change
    # the parties of people in locked constituecies.

    def test_change_party_in_locked_unprivileged_disallowed(self):
        response = self.app.get("/person/4170/update", user=self.user)
        form = response.forms["person-details"]
        form["source"] = "Testing a party change in a locked constituency"
        form["party_GB_parl.2015-05-07"] = self.conservative_party.ec_id
        submission_response = form.submit(expect_errors=True)
        self.assertEqual(submission_response.status_code, 403)

    def test_change_party_in_locked_privileged_allowed(self):
        response = self.app.get(
            "/person/4170/update", user=self.user_who_can_lock
        )
        form = response.forms["person-details"]
        form["source"] = "Testing a party change in a locked constituency"
        form["party_GB_parl.2015-05-07"] = self.conservative_party.ec_id
        submission_response = form.submit()
        self.assertEqual(submission_response.status_code, 302)
        self.assertEqual(submission_response.location, "/person/4170")

    def test_change_party_in_unlocked_unprivileged_allowed(self):
        response = self.app.get("/person/4322/update", user=self.user)
        form = response.forms["person-details"]
        form["source"] = "Testing a party change in an unlocked constituency"
        form["party_GB_parl.2015-05-07"] = self.conservative_party.ec_id
        submission_response = form.submit()
        self.assertEqual(submission_response.status_code, 302)
        self.assertEqual(submission_response.location, "/person/4322")
