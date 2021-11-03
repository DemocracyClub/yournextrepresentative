from django.urls import reverse
from webtest import Text

from people.tests.test_person_view import PersonViewSharedTestsMixin
from candidates.views.version_data import get_change_metadata
from candidates.tests.factories import ElectionFactory, BallotPaperFactory
from people.models import EditLimitationStatuses


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
        version = self.person.versions[0]
        self.assertEqual(version["information_source"], "Mumsnet")

    def test_no_duplicate_versions(self):
        self.person.record_version(get_change_metadata(None, "First update"))
        self.assertEqual(len(self.person.versions), 1)

        self.person.record_version(get_change_metadata(None, "Nothing changed"))
        self.assertEqual(len(self.person.versions), 1)

        self.person.name = "New Name"
        self.person.record_version(get_change_metadata(None, "Nothing changed"))
        self.assertEqual(len(self.person.versions), 2)

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
        self.assertContains(response, "Please enter a valid date.")

    def test_set_birth_date_invalid_date(self):
        """
        Regression for
        https://github.com/DemocracyClub/yournextrepresentative/issues/850
        """

        response = self.app.get(
            "/person/{}/update".format(self.person.pk), user=self.user
        )

        form = response.forms[1]
        form["birth_date"] = "1962"
        form["source"] = "BBC News"
        response = form.submit().follow()
        self.assertContains(response, "1962")

    def test_set_birth_date_year_only(self):
        """
        Regression for
        https://github.com/DemocracyClub/yournextrepresentative/issues/850
        """

        response = self.app.get(
            "/person/{}/update".format(self.person.pk), user=self.user
        )

        form = response.forms[1]
        form["birth_date"] = "1962"
        form["source"] = "BBC News"
        response = form.submit().follow()
        self.assertContains(response, "1962")

    def test_set_dead_person_age(self):
        """
        Regression for
        https://github.com/DemocracyClub/yournextrepresentative/issues/980
        """

        response = self.app.get(
            "/person/{}/update".format(self.person.pk), user=self.user
        )

        form = response.forms[1]
        form["birth_date"] = "1962"
        form["death_date"] = "2000"
        form["source"] = "BBC News"
        form.submit().follow()
        self.person.refresh_from_db()
        self.assertEqual(self.person.age, "37 or 38")

    def test_change_name_creates_other_names(self):
        self.assertFalse(self.person.other_names.exists())
        response = self.app.get(
            "/person/{}/update".format(self.person.pk), user=self.user
        )

        form = response.forms[1]
        form["name"] = "Tessa Palmer"
        form["source"] = "Mumsnet"
        form.submit()
        self.person.refresh_from_db()
        self.assertEqual(self.person.other_names.first().name, "Tessa Jowell")
        self.assertEqual(self.person.name, "Tessa Palmer")

    def test_edits_prevented(self):
        # See if we get a 403 when submitting a person form
        # for a person who's edits are prevented
        response = self.app.get(
            "/person/{}/update/".format(self.person.pk), user=self.user
        )
        form = response.forms[1]
        form["name"] = "Tessa Palmer"
        form["source"] = "Mumsnet"
        self.person.edit_limitations = (
            EditLimitationStatuses.EDITS_PREVENTED.name
        )
        self.person.save()
        response = form.submit(expect_errors=True)
        self.assertEqual(response.status_code, 403)

        # Check no edit button is shown
        response = self.app.get(
            "/person/{}/".format(self.person.pk), user=self.user
        )
        self.assertContains(response, "Edits disabled")
        self.assertNotContains(response, "Edit candidate")

        # Check we can't see the edit form
        response = self.app.get(
            "/person/{}/update/".format(self.person.pk), user=self.user
        )
        self.assertContains(
            response,
            "Editing of this page has been disabled to prevent possible vandalism.",
        )
        self.assertNotContains(response, "<h2>Personal details:</h2>")

    def test_person_update_election_future_not_current(self):
        future_election = ElectionFactory(
            election_date="2050-01-01", slug="parl.2050-01-01", current=False
        )
        ballot = BallotPaperFactory(
            election=future_election,
            post=self.dulwich_post,
            ballot_paper_id="parl.foo.2050-01-01",
        )

        self.person.memberships.create(
            ballot=ballot, post=self.dulwich_post, party=self.green_party
        )

        response = self.app.get(
            "/person/{}/update/".format(self.person.pk), user=self.user
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            set(response.context["form"].initial.keys()),
            {
                "id",
                "honorific_prefix",
                "name",
                "honorific_suffix",
                "gender",
                "birth_date",
                "death_date",
                "biography",
                "favourite_biscuit",
                # "standing_parl.2015-05-07",
                # "constituency_parl.2015-05-07",
                # "party_GB_parl.2015-05-07",
                # "constituency_parl.2050-01-01",
                # "party_GB_parl.2050-01-01",
                # "person",
            },
        )

    def test_person_not_standing_version(self):
        """
        There was a bug where people with a "not_standing" entry couldn't be
        edited due to the way the versions were calculated.

        This is a regression test to catch that previously untested case

        """
        # First set some versions up by making an edit
        response = self.app.get(
            "/person/{}/update".format(self.person.pk), user=self.user
        )

        form = response.forms[1]
        form["favourite_biscuit"] = "Ginger nut"
        form["source"] = "Mumsnet"
        form.submit()

        # Now add to the person's `not_standing` list
        self.person.not_standing.add(self.earlier_election)

        # Now make another edit
        response = self.app.get(
            "/person/{}/update".format(self.person.pk), user=self.user
        )

        form = response.forms[1]
        form["favourite_biscuit"] = "Something else"
        form["source"] = "Somewhere else"

        # The bug this tests for would cause this to raise 500
        response = form.submit().follow()
        self.assertEqual(response.status_code, 200)
        self.person.refresh_from_db()
        version = self.person.versions[0]
        self.assertEqual(version["data"]["not_standing"], ["parl.2010-05-06"])

    def test_person_update_ids_and_add_candidacy(self):
        """
        https://github.com/DemocracyClub/yournextrepresentative/issues/1307

        """
        # First set some versions up by making an edit
        self.assertEqual(self.person.tmp_person_identifiers.count(), 0)
        response = self.app.get(
            "/person/{}/update".format(self.person.pk), user=self.user
        )

        form = response.forms[1]
        form["tmp_person_identifiers-0-value"] = "https://facebook.com/example/"
        form["tmp_person_identifiers-0-value_type"] = "facebook_page_url"

        form["source"] = "Mumsnet"
        form.submit()

        self.person.refresh_from_db()
        self.assertEqual(self.person.tmp_person_identifiers.count(), 1)

        # Not perform the edit that caused the error
        response = self.app.get(
            "/person/{}/update".format(self.person.pk), user=self.user
        )

        future_election = ElectionFactory(
            election_date="2050-01-01", slug="parl.2050-01-01", current=False
        )
        BallotPaperFactory(
            election=future_election,
            post=self.dulwich_post,
            ballot_paper_id="parl.foo.2050-01-01",
        )

        form = response.forms[1]
        extra_fields = [
            ("extra_election_id", "parl.2050-01-01"),
            ("party_GB_parl.2050-01-01", self.labour_party.ec_id),
            ("constituency_parl.2050-01-01", self.dulwich_post.identifier),
            ("standing_parl.2050-01-01", "standing"),
            ("source", "Testing dynamic election addition"),
        ]
        start_pos = len(form.field_order)
        for pos, data in enumerate(extra_fields):
            name, value = data
            field = Text(form, "input", name, start_pos + pos, value)
            form.field_order.append((name, field))
            form.fields[name] = [field]

        form["tmp_person_identifiers-0-value"] = ""
        form["tmp_person_identifiers-0-value_type"] = ""
        form["tmp_person_identifiers-1-value"] = "https://example.com/"
        form["tmp_person_identifiers-1-value_type"] = ""
        form.submit()

    def test_person_create_select_election(self):
        resp = self.app.get(
            reverse("person-create-select-election") + "?name=foo",
            user=self.user,
        )
        self.assertEqual(resp.status_code, 200)
        form = resp.forms["select_ballot_form"]
        form["ballot"] = self.dulwich_post_ballot.ballot_paper_id
        resp = form.submit()
        self.assertEqual(
            resp.url, "/election/parl.65808.2015-05-07/person/create/?name=foo"
        )
