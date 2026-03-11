import textwrap
from unittest.mock import patch

import pytest
from candidates.models import LoggedAction
from candidates.tests.auth import TestUserMixin
from candidates.tests.uk_examples import UK2015ExamplesMixin
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test.utils import override_settings
from django_webtest import WebTest
from official_documents.models import BallotSOPN
from people.helpers import person_names_equal
from people.tests.factories import PersonFactory
from people.tests.test_person_view import PersonViewSharedTestsMixin
from popolo.models import OtherName


class TestOtherNamesViews(TestUserMixin, UK2015ExamplesMixin, WebTest):
    def setUp(self):
        super().setUp()
        self.person_no_other = PersonFactory.create(id=1234, name="John Smith")
        self.person_other_names = PersonFactory.create(id=5678, name="Fozzie")
        self.fozziewig = OtherName.objects.create(
            content_object=self.person_other_names,
            name="Mr Fozziewig",
            note="In a Muppet Christmas Carol",
        )
        self.fozzie_bear = OtherName.objects.create(
            content_object=self.person_other_names,
            name="Fozzie Bear",
            note="Full name",
        )

    # Listing

    def test_list_other_names_no_names(self):
        response = self.app.get("/person/1234/other-names")
        self.assertIn("No alternative names found", response.text)

    def test_list_other_names_some_Names(self):
        response = self.app.get("/person/5678/other-names")
        self.assertIn("<td><strong>Fozzie Bear</strong></td>", response.text)
        self.assertIn("<td><strong>Mr Fozziewig</strong></td>", response.text)

    # Deleting

    def test_delete_other_name_not_authenticated(self):
        # Get the page so we'll have a CSRF token:
        response = self.app.get("/person/5678/other-names")
        url = "/person/5678/other-name/{on_id}/delete".format(
            on_id=self.fozzie_bear.id
        )
        response = self.app.post(
            url,
            params={
                "csrfmiddlewaretoken": self.app.cookies["csrftoken"],
                "source": "Some good reasons for deleting this name",
            },
            expect_errors=True,
        )
        self.assertEqual(response.status_code, 403)

    def test_delete_other_name_authenticated_works(self):
        # Get the page so we'll have a CSRF token:
        response = self.app.get("/person/5678/other-names", user=self.user)

        other_name_id = self.person_other_names.other_names.all()[0].id
        form_id = f"other-name-delete-reason-{other_name_id}"
        form = response.forms[form_id]

        form["source"] = "Some good reasons for deleting this name"
        response = form.submit()

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.location, "/person/5678/other-names")
        self.assertEqual(1, self.person_other_names.other_names.count())
        self.assertEqual(
            self.person_other_names.other_names.get().name, "Mr Fozziewig"
        )

        latest_logged_action = LoggedAction.objects.latest("updated")
        self.assertEqual(
            latest_logged_action.action_type, "person-other-name-delete"
        )
        self.assertEqual(latest_logged_action.person_id, 5678)
        self.assertEqual(
            latest_logged_action.source,
            "Some good reasons for deleting this name",
        )

    # Adding

    def test_add_other_name_get_not_authenticated(self):
        # Get the create page:
        response = self.app.get(
            "/person/5678/other-names/create", expect_errors=True
        )
        self.assertEqual(response.status_code, 403)

    def test_add_other_name_post_not_authenticated(self):
        # Get a page we can view to get the CSRF token:
        response = self.app.get("/person/5678/other-names")
        # Post to the create page:
        response = self.app.post(
            "/person/5678/other-names/create",
            params={
                "name": "J Smith",
                "note": "Name with just initials",
                "csrfmiddlewaretoken": self.app.cookies["csrftoken"],
            },
            expect_errors=True,
        )
        self.assertEqual(response.status_code, 403)

    def test_add_other_name_authenticated_no_source(self):
        # Get a page we can view to get the CSRF token:
        response = self.app.get(
            "/person/5678/other-names/create", user=self.user
        )
        form = response.forms["person_create_other_name"]
        form["name"] = "J Smith"
        submission_response = form.submit()
        self.assertEqual(submission_response.status_code, 200)
        self.assertIn(
            "You forgot to reference a source", submission_response.text
        )

    def test_add_other_name_authenticated_succeeds(self):
        # Get a page we can view to get the CSRF token:
        response = self.app.get(
            "/person/5678/other-names/create", user=self.user
        )
        form = response.forms["person_create_other_name"]
        form["name"] = "F Bear"
        form["source"] = "Some reasonable explanation"
        submission_response = form.submit()
        self.assertEqual(submission_response.status_code, 302)
        self.assertEqual(
            submission_response.location, "/person/5678/other-names"
        )
        self.assertEqual(3, self.person_other_names.other_names.count())

        latest_logged_action = LoggedAction.objects.latest("updated")
        self.assertEqual(
            latest_logged_action.action_type, "person-other-name-create"
        )
        self.assertEqual(latest_logged_action.person_id, 5678)
        self.assertEqual(
            latest_logged_action.source, "Some reasonable explanation"
        )

    # Editing

    def test_edit_other_name_get_not_authenticated(self):
        # Get the edit page:
        response = self.app.get(
            "/person/5678/other-name/{on_id}/update".format(
                on_id=self.fozzie_bear.id
            ),
            expect_errors=True,
        )
        self.assertEqual(response.status_code, 403)

    def test_edit_other_name_post_not_authenticated(self):
        # Get a page we can view to get the CSRF token:
        response = self.app.get("/person/5678/other-names")
        # Post to the edit page:
        response = self.app.post(
            "/person/5678/other-name/{on_id}/update".format(
                on_id=self.fozzie_bear.id
            ),
            params={
                "name": "F Bear",
                "note": "Name with just initials",
                "csrfmiddlewaretoken": self.app.cookies["csrftoken"],
            },
            expect_errors=True,
        )
        self.assertEqual(response.status_code, 403)

    def test_edit_other_name_authenticated_no_source(self):
        # Get a page we can view to get the CSRF token:
        response = self.app.get(
            "/person/5678/other-name/{on_id}/update".format(
                on_id=self.fozzie_bear.id
            ),
            user=self.user,
        )
        form = response.forms["person_update_other_name"]
        form["name"] = "F Bear"
        submission_response = form.submit()
        self.assertEqual(submission_response.status_code, 200)
        self.assertIn(
            "You forgot to reference a source", submission_response.text
        )

    def test_edit_other_name_authenticated_succeeds(self):
        # Get a page we can view to get the CSRF token:
        response = self.app.get(
            "/person/5678/other-name/{on_id}/update".format(
                on_id=self.fozzie_bear.id
            ),
            user=self.user,
        )
        form = response.forms["person_update_other_name"]
        form["name"] = "F Bear"
        form["source"] = "Some reasonable explanation"
        submission_response = form.submit()
        self.assertEqual(submission_response.status_code, 302)
        self.assertEqual(
            submission_response.location, "/person/5678/other-names"
        )
        self.assertEqual(2, self.person_other_names.other_names.count())

        latest_logged_action = LoggedAction.objects.latest("updated")
        self.assertEqual(
            latest_logged_action.action_type, "person-other-name-update"
        )
        self.assertEqual(latest_logged_action.person_id, 5678)
        self.assertEqual(
            latest_logged_action.source, "Some reasonable explanation"
        )

    def test_other_names_on_update_page(self):
        response = self.app.get(
            "/person/{}/update/".format(self.person_other_names.id),
            user=self.user,
        )
        self.assertContains(response, "Also known as Fozzie")

    def test_other_names_add_duplicate(self):
        self.assertEqual(2, self.person_other_names.other_names.count())
        response = self.app.get(
            "/person/{}/other-names/create".format(self.person_other_names.id),
            user=self.user,
        )
        form = response.forms["person_create_other_name"]
        form["name"] = "Fozzie Bear"
        form["source"] = "Some reasonable explanation"
        submission_response = form.submit()
        self.assertEqual(submission_response.status_code, 200)
        self.assertEqual(
            submission_response.context["form"].errors,
            {"name": ["This other name already exists"]},
        )
        self.assertEqual(2, self.person_other_names.other_names.count())

    def test_edit_existing_alt_name_notes_field_regression(self):
        """
        Test for the fix for issue #1242
        https://github.com/DemocracyClub/yournextrepresentative/issues/1242

        """

        # Add a new alt name with a note
        response = self.app.get(
            "/person/5678/other-name/{on_id}/update".format(
                on_id=self.fozzie_bear.id
            ),
            user=self.user,
        )
        form = response.forms["person_update_other_name"]
        form["name"] = "F Bear"
        form["note"] = "Some reasonable explanation"
        form.submit()
        self.assertEqual(self.person_other_names.other_names.count(), 2)

        # Now go and update the note
        response = self.app.get(
            "/person/5678/other-name/{on_id}/update".format(
                on_id=self.fozzie_bear.id
            ),
            user=self.user,
        )
        form = response.forms["person_update_other_name"]
        form["note"] = "A different explanation"
        form["source"] = "Correcting note"
        response = form.submit()
        self.assertEqual(response.status_code, 302)
        self.assertEqual(self.person_other_names.other_names.count(), 2)


class TestSopnNamesViews(PersonViewSharedTestsMixin):
    def test_edit_sopn_names_form_ballot_has_no_sopn(self):
        response = self.app.get(
            "/person/2009/sopn-names/{membership_id}".format(
                membership_id=self.person.memberships.first().id
            ),
            user=self.user,
            expect_errors=True,
        )
        self.assertEqual(response.status_code, 404)

    @patch("candidates.views.other_names.send_sopn_name_change_notification")
    def test_edit_sopn_names_form_ballot_with_sopn_no_notification(
        self, mock_send_sopn_name_change_notification
    ):
        BallotSOPN.objects.create(
            ballot=self.dulwich_post_ballot,
            uploaded_file=SimpleUploadedFile("sopn.pdf", b"fake SOPN content"),
            source_url="example.com",
        )
        resp1 = self.app.get(
            "/person/2009/sopn-names/{membership_id}".format(
                membership_id=self.person.memberships.first().id
            ),
            user=self.user,
        )

        form = resp1.forms["person_edit_sopn_names"]
        form["sopn_last_name"] = "Jowell"
        form["sopn_first_names"] = "Tessa Jane Helen Douglas"
        resp2 = form.submit()

        self.assertEqual(resp2.status_code, 302)
        membership = self.person.memberships.first()
        self.assertEqual(membership.sopn_last_name, "Jowell")
        self.assertEqual(
            membership.sopn_first_names, "Tessa Jane Helen Douglas"
        )

        mock_send_sopn_name_change_notification.assert_not_called()

    @patch("people.notifications.send_mail")
    @override_settings(SOPN_UPDATE_NOTIFICATION_EMAILS=["fred@example.com"])
    @override_settings(BASE_URL="https://candidates.example.com")
    def test_edit_sopn_names_form_ballot_with_sopn_with_notification(
        self, mock_send_mail
    ):
        self.dulwich_post_ballot.candidates_locked = True
        self.dulwich_post_ballot.save()

        BallotSOPN.objects.create(
            ballot=self.dulwich_post_ballot,
            uploaded_file=SimpleUploadedFile("sopn.pdf", b"fake SOPN content"),
            source_url="example.com",
        )

        expected_mail_body = textwrap.dedent(
            """\
            Hello,

            The user john changed the SOPN name of https://candidates.example.com/person/2009/tessa-jowell from "" to "Tessa Jane Helen Douglas Jowell".

            for ballot https://candidates.example.com/elections/parl.65808.2015-05-07/
            """
        )

        resp1 = self.app.get(
            "/person/2009/sopn-names/{membership_id}".format(
                membership_id=self.person.memberships.first().id
            ),
            user=self.user,
        )

        form = resp1.forms["person_edit_sopn_names"]
        form["sopn_last_name"] = "Jowell"
        form["sopn_first_names"] = "Tessa Jane Helen Douglas"
        resp2 = form.submit()

        self.assertEqual(resp2.status_code, 302)

        membership = self.person.memberships.first()
        self.assertEqual(membership.sopn_last_name, "Jowell")
        self.assertEqual(
            membership.sopn_first_names, "Tessa Jane Helen Douglas"
        )

        mock_send_mail.assert_called_once_with(
            "Name for candidate updated",
            expected_mail_body,
            ["fred@example.com"],
        )


@pytest.mark.parametrize(
    "name,other_name,equal",
    [
        ("John Smith", "John Smith", True),
        ("John Smith", "John      Smith", True),
        ("John Smith", "John smith", True),
        ("John Smith", "JoHn smiTh", True),
        ("John Smith", "JoHn Jones", False),
        ("John MacFoo", "John Macfoo", True),
    ],
)
def test_person_names_equal(name, other_name, equal):
    assert person_names_equal(name, other_name) == equal
