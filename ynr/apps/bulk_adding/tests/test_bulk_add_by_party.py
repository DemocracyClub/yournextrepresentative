from django.test.utils import override_settings
from django.core.management import call_command
from django_webtest import WebTest

from candidates.models import LoggedAction
from candidates.tests.auth import TestUserMixin
from candidates.tests.uk_examples import UK2015ExamplesMixin

from candidates.tests.factories import MembershipFactory
from people.tests.factories import PersonFactory


class TestBulkAddingByParty(TestUserMixin, UK2015ExamplesMixin, WebTest):
    def setUp(self):
        super().setUp()
        call_command("rebuild_index", verbosity=0, interactive=False)

    def test_party_select(self):
        response = self.app.get(
            "/bulk_adding/party/parl.2015-05-07/",
            user=self.user_who_can_upload_documents,
        )

        self.assertContains(response, "GB Parties")

    def test_party_select_invalid_party(self):
        form = self.app.get(
            "/bulk_adding/party/parl.2015-05-07/",
            user=self.user_who_can_upload_documents,
        ).forms[1]
        form["party_GB"] = ""
        response = form.submit()
        self.assertContains(response, "Select one and only one party")

    @override_settings(CANDIDATES_REQUIRED_FOR_WEIGHTED_PARTY_LIST=0)
    def test_party_select_non_current_party(self):
        self.person = PersonFactory.create(id=2009, name="Tessa Jowell")
        MembershipFactory.create(
            person=self.person,
            post=self.dulwich_post,
            party=self.labour_party,
            post_election=self.dulwich_post_pee,
        )

        form = self.app.get(
            "/bulk_adding/party/parl.2015-05-07/",
            user=self.user_who_can_upload_documents,
        ).forms[1]
        form["party_GB"].force_value("PP63")
        response = form.submit()
        self.assertEqual(response.status_code, 302)

    def test_submit_party_redirects_to_person_form(self):
        form = self.app.get(
            "/bulk_adding/party/parl.2015-05-07/",
            user=self.user_who_can_upload_documents,
        ).forms[1]
        form["party_GB"] = self.conservative_party.ec_id
        response = form.submit().follow()

        self.assertEqual(response.status_code, 200)

        self.assertContains(response, "Add Conservative Party candidates")

        self.assertEqual(response.context["election_obj"], self.election)

        self.assertTrue(len(response.context["posts"]), 2)

        self.assertContains(response, "Camberwell and Peckham")

        self.assertContains(response, "1 seat contested.")

        self.assertContains(
            response, "No Conservative Party candidates known yet."
        )

    def test_submit_name_for_area_without_source(self):
        pee = self.election.postextraelection_set.first()
        form = self.app.get(
            "/bulk_adding/party/parl.2015-05-07/PP52/",
            user=self.user_who_can_upload_documents,
        ).forms[1]

        form["{}-0-name".format(pee.pk)] = "Pemphero Pasternak"

        response = form.submit()
        self.assertContains(response, "This field is required")
        self.assertContains(response, "Pemphero Pasternak")

    def test_submit_name_for_area_without_any_names(self):
        form = self.app.get(
            "/bulk_adding/party/parl.2015-05-07/PP52/",
            user=self.user_who_can_upload_documents,
        ).forms[1]

        form["source"] = "https://example.com/candidates/"

        response = form.submit()
        self.assertContains(response, "Please enter at least one name")

    def test_submit_name_for_area(self):
        pee = self.election.postextraelection_set.first()
        pee.winner_count = 3
        pee.save()

        # Make sure we have no people or logged actions
        self.assertEqual(pee.post.memberships.count(), 0)
        self.assertEqual(LoggedAction.objects.count(), 0)

        form = self.app.get(
            "/bulk_adding/party/parl.2015-05-07/PP52/", user=self.user
        ).forms[1]

        self.assertEqual(len(form.fields), 25)

        form["source"] = "https://example.com/candidates/"
        form["{}-0-name".format(pee.pk)] = "Pemphero Pasternak"

        response = form.submit().follow()

        self.assertContains(
            response, "Add <strong>Pemphero Pasternak</strong> as a new person"
        )

        form = response.forms[1]

        # Test that the form raises and error if nothing is selected
        response = form.submit()
        self.assertContains(response, "This field is required.")

        # Now submit the valid form
        with self.assertNumQueries(46):
            form["{}-0-select_person".format(pee.pk)] = "_new"
            response = form.submit().follow()

        # We should have a new person and membership
        self.assertTrue(
            pee.post.memberships.first().person.name, "Pemphero Pasternak"
        )

        # We should have a new person and membership
        self.assertTrue(
            pee.post.memberships.first().person.name, "Pemphero Pasternak"
        )

        # We should have created 2 logged actions, one for person-create
        # and one for person-update (adding the membership)
        self.assertEqual(LoggedAction.objects.count(), 2)
