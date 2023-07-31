from candidates.models import LoggedAction
from candidates.tests.auth import TestUserMixin
from candidates.tests.uk_examples import UK2015ExamplesMixin
from django.urls import reverse
from django_webtest import WebTest
from parties.models import Party
from people.models import Person


class TestNewPersonView(TestUserMixin, UK2015ExamplesMixin, WebTest):
    def setUp(self):
        super().setUp()

    def test_new_person_submission(self):
        response = self.app.get(
            self.dulwich_post_ballot.get_absolute_url(), user=self.user
        )

        # make sure we've got the PersonIdentifiers
        self.assertTrue(
            response.html.find(
                "input", {"name": "tmp_person_identifiers-0-value"}
            )
        )

        # make sure we've got the simple personal fields
        self.assertTrue(response.html.find("input", {"id": "id_name"}))

        # make sure we've got the simple demographic fields
        self.assertTrue(response.html.find("input", {"id": "id_gender"}))

        form = response.forms["new-candidate-form"]
        form["name"] = "Elizabeth Bennet"
        form["tmp_person_identifiers-0-value"] = "lizzie@example.com"
        form["tmp_person_identifiers-0-value_type"] = "email"
        form[
            "tmp_person_identifiers-1-value"
        ] = "http://en.wikipedia.org/wiki/Lizzie_Bennet"
        form["tmp_person_identifiers-1-value_type"] = "wikipedia_url"

        form["party_identifier_1"] = self.labour_party.ec_id

        submission_response = form.submit()

        # If there's no source specified, it shouldn't ever get to
        # update_person, and redirect back to the constituency page:
        self.assertEqual(submission_response.status_code, 200)

        self.assertContains(
            submission_response, "You forgot to reference a source"
        )

        form["source"] = "Testing adding a new person to a post"
        submission_response = form.submit()

        person = Person.objects.get(name="Elizabeth Bennet")

        self.assertEqual(person.birth_date, "")

        self.assertEqual(submission_response.status_code, 302)
        self.assertEqual(
            submission_response.location, "/person/{}".format(person.id)
        )

        self.assertEqual(person.name, "Elizabeth Bennet")
        self.assertEqual(person.get_email, "lizzie@example.com")

        self.assertEqual(person.memberships.count(), 1)

        candidacy = person.memberships.first()

        self.assertEqual(candidacy.post.slug, "65808")
        self.assertEqual(candidacy.party.legacy_slug, "party:53")
        self.assertEqual(candidacy.party.ec_id, "PP53")
        self.assertEqual(candidacy.ballot.election_id, self.election.id)

        person_identifiers = person.tmp_person_identifiers.all()
        self.assertEqual(person_identifiers.count(), 2)
        self.assertEqual(
            person_identifiers[1].value,
            "http://en.wikipedia.org/wiki/Lizzie_Bennet",
        )

        self.assertNotEqual(person.versions, [])

        versions = person.versions
        self.assertEqual(len(versions), 1)
        self.assertEqual(
            versions[0]["information_source"],
            "Testing adding a new person to a post",
        )

        last_logged_action = LoggedAction.objects.all().order_by("-created")[0]
        self.assertEqual(last_logged_action.person_id, person.id)
        self.assertEqual(last_logged_action.action_type, "person-create")

    def test_new_person_view(self):
        self.assertFalse(
            Person.objects.filter(name="Elizabeth Bennet").exists()
        )
        url = reverse(
            "person-create",
            kwargs={
                "ballot_paper_id": self.dulwich_post_ballot.ballot_paper_id
            },
        )
        response = self.app.get(url, user=self.user)
        self.assertEqual(response.status_code, 200)

        # make sure we've got the PersonIdentifiers
        self.assertTrue(
            response.html.find(
                "input", {"name": "tmp_person_identifiers-0-value"}
            )
        )
        # make sure we've got the simple personal fields
        self.assertTrue(response.html.find("input", {"id": "id_name"}))

        self.assertTrue(
            response.html.find("input", {"id": "id_ballot_paper_id"})
        )
        self.assertEqual(
            response.html.find("input", {"id": "id_ballot_paper_id"})["value"],
            self.dulwich_post_ballot.ballot_paper_id,
        )
        #
        form = response.forms["new-candidate-form"]
        form["name"] = "Elizabeth Bennet"
        form["party_identifier_1"] = self.labour_party.ec_id
        form["source"] = "Testing adding a new person to a post"
        submission_response = form.submit()
        self.assertEqual(submission_response.status_code, 302)
        self.assertTrue(Person.objects.get(name="Elizabeth Bennet"))

    def test_person_create_does_not_have_spaces_after_saving(self):
        """Test that the name of a person does not have spaces
        before or after the name after creating or editing a person.
        Create a person through the person form and check that the name
        does not have spaces before or after the name.
        """
        url = reverse(
            "person-create",
            kwargs={
                "ballot_paper_id": self.dulwich_post_ballot.ballot_paper_id
            },
        )
        response = self.app.get(url, user=self.user)
        form = response.forms["new-candidate-form"]
        form["name"] = " Elizabeth Bennet "
        form["party_identifier_1"] = self.labour_party.ec_id
        form["source"] = "Testing spaces are stripped out of person name"
        submission_response = form.submit()
        self.assertEqual(submission_response.status_code, 302)
        self.assertTrue(Person.objects.get(name="Elizabeth Bennet"))

    def test_party_identifier_has_choices(self):
        url = reverse(
            "person-create",
            kwargs={
                "ballot_paper_id": self.dulwich_post_ballot.ballot_paper_id
            },
        )
        response = self.app.get(url, user=self.user)
        form = response.forms["new-candidate-form"]
        # get the display value from the party choices loaded by the form
        party_choices = [
            party[-1] for party in form["party_identifier_0"].options
        ]
        # get all party names from the db
        party_names = Party.objects.values_list("name", flat=True)
        # check parties are in the choices
        for name in party_names:
            with self.subTest(msg=name):
                self.assertIn(name, party_choices)
