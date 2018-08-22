import re
from django.utils.six.moves.urllib_parse import urlsplit
from django.conf import settings

from django_webtest import WebTest
from popolo.models import Person

from popolo.models import Person

from .auth import TestUserMixin
from .uk_examples import UK2015ExamplesMixin

from ynr_refactoring.helpers.popolo_fields import SimplePopoloField


def get_next_dd(start):
    return [t for t in start.next_siblings if t.name == "dd"][0]


class SimpleFieldsTests(TestUserMixin, UK2015ExamplesMixin, WebTest):
    def setUp(self):
        super().setUp()
        field = SimplePopoloField(
            name="additional_name",
            label="Additional Name",
            info_type_key="text",
            order=4,
        )
        if field not in settings.SIMPLE_POPOLO_FIELDS:
            settings.SIMPLE_POPOLO_FIELDS.append(field)

        # Create one person with these fields already present:
        self.person = Person.objects.create(
            name="John the Well-Described",
            additional_name="Very Well-Described",
            versions="[]",
        )

    def test_create_form_has_fields(self):
        response = self.app.get("/election/2015/person/create/", user=self.user)
        self.assertEqual(response.status_code, 200)
        an_label = response.html.find("label", {"for": "id_additional_name"})
        self.assertIsNotNone(an_label)
        an_input = response.html.find("input", {"id": "id_additional_name"})
        self.assertIsNotNone(an_input)

    def test_update_form_is_prefilled(self):
        response = self.app.get(
            "/person/{person_id}/update".format(person_id=self.person.id),
            user=self.user,
        )
        an_label = response.html.find("label", {"for": "id_additional_name"})
        self.assertIsNotNone(an_label)
        an_input = response.html.find("input", {"id": "id_additional_name"})
        self.assertIsNotNone(an_input)
        self.assertEqual(an_input.get("value"), "Very Well-Described")

    def test_fields_are_saved_when_editing(self):
        response = self.app.get(
            "/person/{person_id}/update".format(person_id=self.person.id),
            user=self.user,
        )
        form = response.forms["person-details"]
        form["additional_name"] = "An extra name"
        form["source"] = "Testing setting simple fields"
        submission_response = form.submit()

        self.assertEqual(submission_response.status_code, 302)
        split_location = urlsplit(submission_response.location)
        self.assertEqual(
            "/person/{person_id}".format(person_id=self.person.id),
            split_location.path,
        )

        person = Person.objects.get(id=self.person.id)
        self.assertEqual(person.additional_name, "An extra name")

    def test_fields_are_saved_when_creating(self):
        response = self.app.get("/election/2015/person/create/", user=self.user)
        form = response.forms["new-candidate-form"]
        form["name"] = "Naomi Newperson"
        form["additional_name"] = "Naomi Newcomer"
        form["standing_2015"] = "not-standing"
        form["source"] = "Test creating someone with simple fields"
        submission_response = form.submit()

        self.assertEqual(submission_response.status_code, 302)
        split_location = urlsplit(submission_response.location)
        m = re.search(r"^/person/(.*)", split_location.path)
        self.assertTrue(m)

        person = Person.objects.get(id=m.group(1))
        self.assertEqual(person.additional_name, "Naomi Newcomer")

    def test_view_additional_fields(self):
        response = self.app.get(
            "/person/{person_id}".format(person_id=self.person.id)
        )

        an_dt = response.html.find("dt", text=u"Also known as")
        an_dd = get_next_dd(an_dt)
        self.assertEqual(
            an_dd.text.strip(), "Very Well-Described (additional name)"
        )
