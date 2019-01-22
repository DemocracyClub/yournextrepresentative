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
