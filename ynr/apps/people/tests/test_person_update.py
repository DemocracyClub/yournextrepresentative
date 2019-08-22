import json

from candidates.tests.person_view_shared_tests_mixin import (
    PersonViewSharedTestsMixin,
)
from candidates.views.version_data import get_change_metadata


class TestPersonUpdate(PersonViewSharedTestsMixin):
    def test_update_favourite_biscuit(self):
        self.assertIsNone(self.person.favourite_biscuit)

        response = self.app.get(
            "/person/{}/update".format(self.person.pk), user=self.user
        )

        form = response.forms[1]
        form["favourite_biscuit"] = "Ginger nut"
        form["source"] = "Mumsnet"
        form.submit()

        self.person.refresh_from_db()
        self.assertEqual(self.person.favourite_biscuit, "Ginger nut")
        version = json.loads(self.person.versions)[0]
        self.assertEqual(version["information_source"], "Mumsnet")

    def test_no_duplicate_versions(self):
        self.person.record_version(get_change_metadata(None, "First update"))
        self.assertEqual(len(json.loads(self.person.versions)), 1)

        self.person.record_version(get_change_metadata(None, "Nothing changed"))
        self.assertEqual(len(json.loads(self.person.versions)), 1)

        self.person.name = "New Name"
        self.person.record_version(get_change_metadata(None, "Nothing changed"))
        self.assertEqual(len(json.loads(self.person.versions)), 2)

    def test_set_death_date(self):
        self.assertEqual(self.person.death_date, "")

        response = self.app.get(
            "/person/{}/update".format(self.person.pk), user=self.user
        )

        form = response.forms[1]
        form["death_date"] = "2017-01-01"
        form["source"] = "BBC News"
        form.submit()

        self.person.refresh_from_db()
        self.assertEqual(self.person.death_date, "2017-01-01")

    def test_set_death_date_different_formats(self):
        date_formats = ["23 July 2019", "23/07/2019"]
        for date_format in date_formats:
            response = self.app.get(
                "/person/{}/update".format(self.person.pk), user=self.user
            )

            form = response.forms[1]
            form["death_date"] = date_format
            form["source"] = "BBC News"
            form.submit()

    def test_set_death_date_too_long(self):

        response = self.app.get(
            "/person/{}/update".format(self.person.pk), user=self.user
        )

        form = response.forms[1]
        form["death_date"] = ("a really really really long string",)
        form["source"] = "BBC News"
        response = form.submit()
        self.assertContains(response, "The date entered was too long")

    def change_name_creates_other_names(self):
        self.assertFalse(self.person.other_names.exists())
        response = self.app.get(
            "/person/{}/update".format(self.person.pk), user=self.user
        )

        form = response.forms[1]
        form["name"] = "Tessa Palmer"
        form["source"] = "Mumsnet"
        form.submit()
        self.assertEqual(self.person.other_names.first().name, "Tessa Jowell")
        self.assertEqual(self.person.name, "Tessa Palmer")
