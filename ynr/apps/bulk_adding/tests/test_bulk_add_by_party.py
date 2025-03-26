from candidates.models import LoggedAction
from candidates.tests.auth import TestUserMixin
from candidates.tests.factories import MembershipFactory
from candidates.tests.uk_examples import UK2015ExamplesMixin
from django_webtest import WebTest
from people.tests.factories import PersonFactory
from utils.testing_utils import FuzzyInt


class TestBulkAddingByParty(TestUserMixin, UK2015ExamplesMixin, WebTest):
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
        form["party_GB_1"] = ""
        form["party_GB_0"] = ""
        response = form.submit()
        self.assertContains(response, "Select one and only one party")

    def test_party_select_non_current_party(self):
        self.person = PersonFactory.create(id=2009, name="Tessa Jowell")
        MembershipFactory.create(
            person=self.person,
            post=self.dulwich_post,
            party=self.labour_party,
            ballot=self.dulwich_post_ballot,
        )

        form = self.app.get(
            "/bulk_adding/party/parl.2015-05-07/",
            user=self.user_who_can_upload_documents,
        ).forms[1]
        form["party_GB_1"] = "PP63"
        response = form.submit()
        self.assertEqual(response.status_code, 302)

    def test_submit_party_redirects_to_person_form(self):
        form = self.app.get(
            "/bulk_adding/party/parl.2015-05-07/",
            user=self.user_who_can_upload_documents,
        ).forms[1]
        form["party_GB_1"] = self.conservative_party.ec_id
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
        ballot = self.election.ballot_set.first()
        form = self.app.get(
            "/bulk_adding/party/parl.2015-05-07/PP52/",
            user=self.user_who_can_upload_documents,
        ).forms[1]

        form["{}-0-name".format(ballot.pk)] = "Pemphero Pasternak"

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
        ballot = self.election.ballot_set.first()
        ballot.winner_count = 3
        ballot.save()
        # Make sure we have no people or logged actions
        self.assertEqual(ballot.post.memberships.count(), 0)
        self.assertEqual(LoggedAction.objects.count(), 0)

        form = self.app.get(
            "/bulk_adding/party/parl.2015-05-07/PP52/", user=self.user
        ).forms[1]

        self.assertEqual(len(form.fields), 79)

        form["source"] = "https://example.com/candidates/"
        form["{}-0-name".format(ballot.pk)] = "Pemphero Pasternak"

        response = form.submit().follow()

        self.assertContains(
            response, '<label>Add a new profile "Pemphero Pasternak"</label>'
        )

        form = response.forms[1]
        # Now submit the valid form
        with self.assertNumQueries(FuzzyInt(49, 72)):
            form["{}-0-select_person".format(ballot.pk)] = "_new"
            response = form.submit().follow()

        # We should have a new person and membership
        self.assertEqual(
            ballot.post.memberships.first().person.name, "Pemphero Pasternak"
        )

        # We should have created 2 logged actions, one for person-create
        # and one for person-update (adding the membership)
        self.assertEqual(LoggedAction.objects.count(), 2)

    def test_submit_name_and_demographic_details_for_area(self):
        ballot = self.election.ballot_set.first()
        ballot.winner_count = 3
        ballot.save()
        # Make sure we have no people or logged actions
        self.assertEqual(ballot.post.memberships.count(), 0)
        self.assertEqual(LoggedAction.objects.count(), 0)

        form = self.app.get(
            "/bulk_adding/party/parl.2015-05-07/PP52/", user=self.user
        ).forms[1]

        self.assertEqual(len(form.fields), 79)

        form["source"] = "https://example.com/candidates/"
        form["{}-0-name".format(ballot.pk)] = "Pemphero Pasternak"
        form["{}-0-biography".format(ballot.pk)] = "Foo"
        form["{}-0-gender".format(ballot.pk)] = "male"
        form["{}-0-birth_date".format(ballot.pk)] = 1987

        response = form.submit().follow()

        self.assertContains(
            response, '<label>Add a new profile "Pemphero Pasternak"</label>'
        )

        form = response.forms[1]
        # Now submit the valid form
        with self.assertNumQueries(FuzzyInt(49, 72)):
            form["{}-0-select_person".format(ballot.pk)] = "_new"
            response = form.submit().follow()

        # We should have a new person with demographic details and membership
        new_person = ballot.post.memberships.first().person
        self.assertEqual(new_person.name, "Pemphero Pasternak")
        self.assertEqual(new_person.biography, "Foo")
        self.assertEqual(new_person.gender, "male")
        self.assertEqual(new_person.birth_date, "1987")

        # We should have created 2 logged actions, one for person-create
        # and one for person-update (adding the membership)
        self.assertEqual(LoggedAction.objects.count(), 2)

    def test_submit_name_and_social_media_links_for_area(self):
        ballot = self.election.ballot_set.first()
        ballot.winner_count = 3
        ballot.save()
        # Make sure we have no people or logged actions
        self.assertEqual(ballot.post.memberships.count(), 0)
        self.assertEqual(LoggedAction.objects.count(), 0)

        form = self.app.get(
            "/bulk_adding/party/parl.2015-05-07/PP52/", user=self.user
        ).forms[1]

        self.assertEqual(len(form.fields), 79)

        form["source"] = "https://example.com/candidates/"
        form[f"{ballot.pk}-0-name"] = "Pemphero Pasternak"
        form[f"{ballot.pk}-0-person_identifiers_0_0"] = "https://example.com"
        form[f"{ballot.pk}-0-person_identifiers_0_1"] = "homepage_url"
        form[f"{ballot.pk}-0-person_identifiers_1_0"] = "pp@gmail.com"
        form[f"{ballot.pk}-0-person_identifiers_1_1"] = "email"
        form[f"{ballot.pk}-0-person_identifiers_2_0"] = (
            "https://linkedin.com/in/pamphero"
        )
        form[f"{ballot.pk}-0-person_identifiers_2_1"] = "linkedin_url"

        response = form.submit().follow()

        self.assertContains(
            response, '<label>Add a new profile "Pemphero Pasternak"</label>'
        )

        form = response.forms[1]
        # Now submit the valid form
        with self.assertNumQueries(FuzzyInt(49, 72)):
            form["{}-0-select_person".format(ballot.pk)] = "_new"
            response = form.submit().follow()

        # We should have a new person with demographic details and membership
        new_person = ballot.post.memberships.first().person
        self.assertEqual(new_person.name, "Pemphero Pasternak")
        pids = new_person.tmp_person_identifiers.count()
        self.assertEqual(pids, 3)

        # We should have created 2 logged actions, one for person-create
        # and one for person-update (adding the membership)
        self.assertEqual(LoggedAction.objects.count(), 2)

    def test_submit_social_media_link_without_link_type(self):
        ballot = self.election.ballot_set.first()
        form = self.app.get(
            "/bulk_adding/party/parl.2015-05-07/PP52/",
            user=self.user_who_can_upload_documents,
        ).forms[1]

        form["source"] = "https://example.com/candidates/"

        # Fill in the link field but don't select the link type
        form[f"{ballot.pk}-0-name"] = "Pemphero Pasternak"
        form[f"{ballot.pk}-0-person_identifiers_0_0"] = "https://example.com"

        response = form.submit()
        self.assertContains(response, "Please select a link type")

    def test_submit_social_media_link_type_without_link(self):
        ballot = self.election.ballot_set.first()
        form = self.app.get(
            "/bulk_adding/party/parl.2015-05-07/PP52/",
            user=self.user_who_can_upload_documents,
        ).forms[1]

        form["source"] = "https://example.com/candidates/"

        # Select a link type but leave link field blank
        form[f"{ballot.pk}-0-name"] = "Pemphero Pasternak"
        form[f"{ballot.pk}-0-person_identifiers_0_1"] = "mastodon_username"

        response = form.submit()
        self.assertContains(response, "Please enter a social media link")

    def test_submit_social_media_link_invalid_url(self):
        ballot = self.election.ballot_set.first()
        form = self.app.get(
            "/bulk_adding/party/parl.2015-05-07/PP52/",
            user=self.user_who_can_upload_documents,
        ).forms[1]

        form["source"] = "https://example.com/candidates/"

        form[f"{ballot.pk}-0-name"] = "Pemphero Pasternak"
        form[f"{ballot.pk}-0-person_identifiers_0_0"] = "https://example"

        form[f"{ballot.pk}-0-person_identifiers_0_1"] = "homepage_url"

        response = form.submit()
        self.assertContains(response, "Enter a valid URL")
