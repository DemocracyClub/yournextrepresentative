from candidates.models import LoggedAction, PersonRedirect
from candidates.models.db import ActionType
from django.urls import reverse
from django_webtest import WebTest
from people.models import Person
from people.tests.factories import PersonFactory

from .test_splitting_suggest import SplitSuggestionMixin, on


class SplitViewMixin(SplitSuggestionMixin):
    def setUp(self):
        super().setUp()
        self.jo = self.make_person(
            "Jo Smith",
            "2026-01-01",
            [(self.dulwich_post_ballot_earlier, self.labour_party)],
        )
        self.joanne = self.make_person(
            "Joanne Smith",
            "2026-02-01",
            [(self.local_ballot, self.green_party)],
            identifiers={"email": "joanne@example.com"},
        )
        self.joanne_pk = self.joanne.pk
        self.merge(self.jo, self.joanne)
        self.jo.refresh_from_db()
        self.split_url = reverse(
            "person-split", kwargs={"person_id": self.jo.pk}
        )

    def membership_value(self, ballot):
        return str(self.jo.memberships.get(ballot=ballot).pk)

    def preview(self, **choices):
        response = self.app.get(self.split_url, user=self.user_who_can_split)
        form = response.forms["person-split"]
        form["membership"] = self.membership_value(self.local_ballot)
        for name, value in choices.items():
            form[name] = value
        with on("2026-09-28"):
            return form.submit("action", value="preview")


class TestSplitButton(SplitViewMixin, WebTest):
    def test_shown_to_splitters_when_more_than_one_candidacy(self):
        response = self.app.get(
            self.jo.get_absolute_url(), user=self.user_who_can_split
        )
        self.assertIn(self.split_url, response.text)

    def test_hidden_from_other_users(self):
        response = self.app.get(self.jo.get_absolute_url(), user=self.user)
        self.assertNotIn(self.split_url, response.text)

    def test_hidden_with_one_candidacy(self):
        self.jo.memberships.filter(ballot=self.local_ballot).delete()
        response = self.app.get(
            self.jo.get_absolute_url(), user=self.user_who_can_split
        )
        self.assertNotIn(self.split_url, response.text)

    def test_page_needs_split_permission(self):
        response = self.app.get(self.split_url, user=self.user, status=403)
        self.assertEqual(response.status_code, 403)

    def test_merging_rights_are_not_enough(self):
        # Splitting has its own group, so it can be rolled out separately
        response = self.app.get(
            self.jo.get_absolute_url(), user=self.user_who_can_merge
        )
        self.assertNotIn(self.split_url, response.text)
        self.app.get(self.split_url, user=self.user_who_can_merge, status=403)


class TestSplitView(SplitViewMixin, WebTest):
    def test_preview_changes_nothing(self):
        response = self.preview()
        report = response.html.find("table", class_="split-report")
        self.assertEqual(
            [td.get_text(strip=True) for td in report.find_all("td")],
            [
                str(self.jo.pk),
                self.local_ballot.ballot_paper_id,
                f"{self.joanne_pk} (restored)",
                "Ready to split",
            ],
        )
        # The rest is tucked away in the details element
        details = response.html.find("details", class_="split-details")
        self.assertIn("Where each detail goes", details.get_text())
        self.assertIn(
            f"This candidacy was added when person {self.joanne_pk} was merged",
            response.text,
        )
        self.assertIn(
            f"Restore person {self.joanne_pk} (old ID)", response.text
        )
        self.assertIn("joanne@example.com", response.text)
        self.assertFalse(Person.objects.filter(pk=self.joanne_pk).exists())
        self.assertFalse(
            LoggedAction.objects.filter(
                action_type=ActionType.PERSON_SPLIT
            ).exists()
        )

    def test_split_after_preview(self):
        response = self.preview()
        form = response.forms["person-split"]
        with on("2026-09-28"):
            response = form.submit("action", value="split").follow()

        restored = Person.objects.get(pk=self.joanne_pk)
        self.assertEqual(response.request.path, restored.get_absolute_url())
        self.assertIn(
            f"Moved {self.local_ballot.ballot_paper_id}", response.text
        )
        self.assertEqual(restored.memberships.get().ballot, self.local_ballot)
        self.assertEqual(
            restored.get_single_identifier_value("email"), "joanne@example.com"
        )
        self.assertFalse(
            PersonRedirect.objects.filter(old_person_id=self.joanne_pk).exists()
        )
        self.assertEqual(
            LoggedAction.objects.get(action_type=ActionType.PERSON_SPLIT).user,
            self.user_who_can_split,
        )

    def test_override_a_field_before_splitting(self):
        response = self.preview()
        form = response.forms["person-split"]
        form["override_email"] = "keep"
        with on("2026-09-28"):
            response = form.submit("action", value="preview")
        self.assertIn("You chose to keep it on this person", response.text)
        form = response.forms["person-split"]
        with on("2026-09-28"):
            form.submit("action", value="split").follow()

        restored = Person.objects.get(pk=self.joanne_pk)
        self.assertIsNone(restored.get_single_identifier_value("email"))
        self.jo.refresh_from_db()
        self.assertEqual(
            self.jo.get_single_identifier_value("email"), "joanne@example.com"
        )

    def test_changed_choices_need_a_new_preview(self):
        response = self.preview()
        form = response.forms["person-split"]
        form["override_email"] = "keep"
        with on("2026-09-28"):
            response = form.submit("action", value="split")
        self.assertEqual(response.status_code, 200)
        self.assertIn("have changed since the preview", response.text)
        self.assertFalse(Person.objects.filter(pk=self.joanne_pk).exists())

    def test_person_edited_since_preview(self):
        response = self.preview()
        form = response.forms["person-split"]
        self.jo.tmp_person_identifiers.create(
            value_type="twitter_username", value="jo"
        )
        self.record(self.jo, "2026-09-27")
        with on("2026-09-28"):
            response = form.submit("action", value="split")
        self.assertIn("have changed since the preview", response.text)
        self.assertFalse(Person.objects.filter(pk=self.joanne_pk).exists())

    def test_warnings_must_be_checked(self):
        # Leaving the original person with no candidacies gives a warning
        self.jo.memberships.filter(
            ballot=self.dulwich_post_ballot_earlier
        ).delete()
        self.record(self.jo, "2026-09-27")
        response = self.preview()
        self.assertIn("split-warnings", response.text)
        self.assertIn("will have no candidacies left", response.text)

        form = response.forms["person-split"]
        with on("2026-09-28"):
            response = form.submit("action", value="split")
        self.assertIn("confirm you&#x27;ve checked the warnings", response.text)
        self.assertFalse(Person.objects.filter(pk=self.joanne_pk).exists())

        form = response.forms["person-split"]
        form["warnings_checked"] = True
        with on("2026-09-28"):
            form.submit("action", value="split").follow()
        self.assertTrue(Person.objects.filter(pk=self.joanne_pk).exists())

    def test_locked_ballot_is_a_warning(self):
        # Moving candidacies on locked ballots is what the page is for, so
        # it's allowed, but has to be acknowledged
        self.local_ballot.candidates_locked = True
        self.local_ballot.save()
        response = self.preview()
        warnings = response.html.find(class_="split-warnings").get_text()
        self.assertIn(
            f"{self.local_ballot.ballot_paper_id} is locked: this split "
            "changes a locked ballot",
            warnings,
        )
        self.assertIn('value="split"', response.text)

        form = response.forms["person-split"]
        form["warnings_checked"] = True
        with on("2026-09-28"):
            form.submit("action", value="split").follow()
        self.assertEqual(
            Person.objects.get(pk=self.joanne_pk).memberships.get().ballot,
            self.local_ballot,
        )

    def test_errors_block_splitting(self):
        other = PersonFactory()
        other.memberships.create(
            ballot=self.local_ballot, party=self.labour_party
        )
        response = self.preview(destination=str(other.pk))
        self.assertIn("split-errors", response.text)
        self.assertIn("is already standing", response.text)
        self.assertIn("Can&#x27;t split", response.text)
        self.assertNotIn('value="split"', response.text)

    def test_move_to_existing_person(self):
        other = PersonFactory(name="Joanne Smith")
        response = self.preview(destination=str(other.pk))
        report = response.html.find("table", class_="split-report")
        self.assertIn(str(other.pk), report.get_text())
        form = response.forms["person-split"]
        with on("2026-09-28"):
            form.submit("action", value="split").follow()
        self.assertEqual(other.memberships.get().ballot, self.local_ballot)
        self.assertFalse(Person.objects.filter(pk=self.joanne_pk).exists())

    def test_destination_can_be_a_person_url(self):
        other = PersonFactory(name="Joanne Smith")
        response = self.preview(
            destination=f"http://localhost:8080/person/{other.pk}/joanne-smith"
        )
        form = response.forms["person-split"]
        with on("2026-09-28"):
            form.submit("action", value="split").follow()
        self.assertEqual(other.memberships.get().ballot, self.local_ballot)

    def test_bad_destination(self):
        response = self.preview(destination="999999")
        self.assertIn("There&#x27;s no person with ID 999999", response.text)
        response = self.preview(destination="someone")
        self.assertIn("Enter “new” or a person ID", response.text)
