import json

from django.utils.six.moves.urllib_parse import urlsplit

from django_webtest import WebTest

from people.models import Person

from candidates.models import LoggedAction

from .auth import TestUserMixin
from .uk_examples import UK2015ExamplesMixin


class TestNewPersonView(TestUserMixin, UK2015ExamplesMixin, WebTest):
    def setUp(self):
        super().setUp()

    def test_new_person_submission_refused_copyright(self):
        # Just a smoke test for the moment:
        response = self.app.get(
            "/constituency/65808/dulwich-and-west-norwood",
            user=self.user_refused,
        )
        split_location = urlsplit(response.location)
        self.assertEqual("/copyright-question", split_location.path)
        self.assertEqual(
            "next=/constituency/65808/dulwich-and-west-norwood",
            split_location.query,
        )

    def test_new_person_submission(self):
        response = self.app.get(
            self.dulwich_post_pee.get_absolute_url(), user=self.user
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

        form["party_GB_2015"] = self.labour_party.ec_id

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
        self.assertEqual(candidacy.role, "Candidate")
        self.assertEqual(candidacy.party.legacy_slug, "party:53")
        self.assertEqual(candidacy.party.ec_id, "PP53")
        self.assertEqual(candidacy.post_election.election_id, self.election.id)

        person_identifiers = person.tmp_person_identifiers.all()
        self.assertEqual(person_identifiers.count(), 2)
        self.assertEqual(
            person_identifiers[1].value,
            "http://en.wikipedia.org/wiki/Lizzie_Bennet",
        )

        self.assertNotEqual(person.versions, "[]")

        versions = json.loads(person.versions)
        self.assertEqual(len(versions), 1)
        self.assertEqual(
            versions[0]["information_source"],
            "Testing adding a new person to a post",
        )

        last_logged_action = LoggedAction.objects.all().order_by("-created")[0]
        self.assertEqual(last_logged_action.person_id, person.id)
        self.assertEqual(last_logged_action.action_type, "person-create")
