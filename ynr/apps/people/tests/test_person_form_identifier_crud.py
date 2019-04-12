from django_webtest import WebTest

from django.core.urlresolvers import reverse
from django.test import override_settings

from candidates.tests.auth import TestUserMixin
from people.models import PersonIdentifier
from people.tests.factories import PersonFactory
from candidates.tests.factories import faker_factory


@override_settings(TWITTER_APP_ONLY_BEARER_TOKEN=None)
class PersonFormsIdentifierCRUDTestCase(TestUserMixin, WebTest):
    def setUp(self):
        # super().setUp()
        self.person = PersonFactory(name=faker_factory.name())
        self.pi = PersonIdentifier.objects.create(
            person=self.person, value="democlub", value_type="twitter_username"
        )

    def test_person_identifier_on_form(self):
        """
        Test that the PersonIdentifier is listed on the Person form.
        """
        resp = self.app.get(
            reverse("person-update", kwargs={"person_id": self.person.pk}),
            user=self.user,
        )

        pi_form = resp.context["identifiers_formset"].initial_forms[0]

        self.assertEqual(pi_form["value"].value(), "democlub")
        self.assertEqual(pi_form["value_type"].value(), "twitter_username")

    def test_form_can_add_new_pi(self):
        resp = self.app.get(
            reverse("person-update", kwargs={"person_id": self.person.pk}),
            user=self.user,
        )

        form = resp.forms[1]
        form["source"] = "Adding a home page"
        form["tmp_person_identifiers-1-value"] = "https://democracyclub.org.uk"
        form["tmp_person_identifiers-1-value_type"] = "homepage_url"
        form.submit()

        self.assertEqual(PersonIdentifier.objects.all().count(), 2)
        self.assertEqual(
            list(PersonIdentifier.objects.values_list("value", flat=True)),
            ["https://democracyclub.org.uk", "democlub"],
        )

    def test_form_can_update_pi(self):
        """
        Test that the PersonIdentifier can be updated
        """
        resp = self.app.get(
            reverse("person-update", kwargs={"person_id": self.person.pk}),
            user=self.user,
        )

        form = resp.forms[1]
        form["source"] = "They changed their username"
        form["tmp_person_identifiers-0-value"] = "@democracyclub"
        form.submit()

        pi = PersonIdentifier.objects.get()
        self.assertEqual(pi.value, "democracyclub")
        self.assertEqual(pi.value_type, "twitter_username")

    def test_form_can_delete_pi(self):
        """
        Test that the PersonIdentifier can be deleted by removing the value
        """
        resp = self.app.get(
            reverse("person-update", kwargs={"person_id": self.person.pk}),
            user=self.user,
        )

        form = resp.forms[1]
        form["source"] = "They deleted their account"
        form["tmp_person_identifiers-0-value"] = ""
        form.submit()

        self.assertFalse(PersonIdentifier.objects.exists())

    def test_form_valid_when_extra_value_type_selected(self):
        """
        If someone selects a value type but doesn't enter a value, it's still valid
        """
        resp = self.app.get(
            reverse("person-update", kwargs={"person_id": self.person.pk}),
            user=self.user,
        )

        form = resp.forms[1]
        form["source"] = "Just picking something from the dropdown"
        form["tmp_person_identifiers-1-value_type"] = "twitter_username"
        resp = form.submit()
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(
            resp.location,
            reverse("person-view", kwargs={"person_id": self.person.pk}),
        )

        self.assertEqual(PersonIdentifier.objects.get().value, "democlub")

    def test_change_value_type(self):
        """
        The value stays the same, but the type changes
        """
        self.assertEqual(
            PersonIdentifier.objects.get().value_type, "twitter_username"
        )
        resp = self.app.get(
            reverse("person-update", kwargs={"person_id": self.person.pk}),
            user=self.user,
        )

        form = resp.forms[1]
        form["source"] = "Just picking something from the dropdown"
        form["tmp_person_identifiers-0-value_type"] = "homepage_url"
        resp = form.submit()
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(
            resp.location,
            reverse("person-view", kwargs={"person_id": self.person.pk}),
        )

        self.assertEqual(
            PersonIdentifier.objects.get().value_type, "homepage_url"
        )

    def _submit_values(self, value, value_type="twitter_username"):
        resp = self.app.get(
            reverse("person-update", kwargs={"person_id": self.person.pk}),
            user=self.user,
        )

        form = resp.forms[1]
        form["source"] = "They changed their username"
        form["tmp_person_identifiers-0-value_type"] = value_type
        form["tmp_person_identifiers-0-value"] = value
        form.submit()
        return form.submit()

    def test_twitter_bad_url(self):
        resp = self._submit_values("http://example.com/blah")
        form = resp.context["identifiers_formset"]
        self.assertFalse(form.is_valid())
        self.assertEqual(
            form[0].non_field_errors(),
            [
                "The Twitter username must only consist of alphanumeric characters or underscore"
            ],
        )

    def test_twitter_full_url(self):
        resp = self._submit_values("https://twitter.com/madeuptwitteraccount")
        self.assertEqual(resp.status_code, 302)

        self.assertEqual(
            PersonIdentifier.objects.get().value, "madeuptwitteraccount"
        )

    def test_bad_email_address(self):
        resp = self._submit_values("whoops", "email")
        form = resp.context["identifiers_formset"]
        self.assertFalse(form.is_valid())
        self.assertEqual(
            form[0].non_field_errors(), ["Enter a valid email address."]
        )
