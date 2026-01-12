import textwrap
from unittest.mock import patch

from candidates.tests.factories import BallotPaperFactory, ElectionFactory
from candidates.views.version_data import get_change_metadata
from django.contrib.auth.models import User
from django.test.utils import override_settings
from django.urls import reverse
from django.utils import timezone
from freezegun import freeze_time
from people.models import EditLimitationStatuses, Person
from people.tests.test_person_view import PersonViewSharedTestsMixin
from webtest import Text


class TestPersonUpdate(PersonViewSharedTestsMixin):
    def test_update_favourite_biscuit(self):
        self.assertIsNone(self.person.favourite_biscuit)

        response = self.app.get(
            "/person/{}/update".format(self.person.pk), user=self.user
        )

        form = response.forms["person-details"]
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

    def test_set_birth_date_invalid_date(self):
        """
        Regression for
        https://github.com/DemocracyClub/yournextrepresentative/issues/850
        """

        response = self.app.get(
            "/person/{}/update".format(self.person.pk), user=self.user
        )

        form = response.forms["person-details"]
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

        form = response.forms["person-details"]
        form["birth_date"] = "1962"
        form["source"] = "BBC News"
        response = form.submit().follow()
        self.assertContains(response, "1962")

    def test_user_cannot_review_person_name(self):
        # current user is not in the TRUSTED_TO_EDIT_NAME group
        # visit the moderation page and return a 403
        response = self.app.get(
            "/moderation/person_name_review/",
            user=self.user,
            expect_errors=True,
        )
        self.assertEqual(response.status_code, 403)

    def test_user_can_review_person_name(self):
        # Test that a user who is in the TRUSTED_TO_EDIT_NAME group
        # can visit the moderation page and see the page
        self.user = User.objects.get(username="george")
        response = self.app.get(
            "/moderation/person_name_review/", user=self.user
        )
        self.assertContains(response, "Review person name suggestions")

    @patch("people.models.send_name_change_notification")
    def test_change_name_by_untrusted_user_no_locked_ballots(
        self, mock_send_name_change_notification
    ):
        # Test that a user who is not in the TRUSTED_TO_EDIT_NAME group
        # makes a change to a person's name (who does not have current, locked ballots),
        # the change is saved directly and an other name is created and not
        # flagged for review
        response = self.app.get(
            "/person/{}/update".format(self.person.pk), user=self.user
        )

        # confirm the original name prior to edits
        self.assertEqual(self.person.name, "Tessa Jowell")
        form = response.forms["person-details"]
        form["name"] = "Tessa Palmer"
        # make a change to another field to ensure that edit is saved
        # regardless of name change
        form["birth_date"] = 1950
        form["source"] = "Mumsnet"
        form.submit()
        self.person.refresh_from_db()
        self.assertEqual(self.person.name, "Tessa Palmer")
        # check that the suggested name has not been created
        self.assertEqual(self.person.other_names.count(), 1)
        self.assertEqual(self.person.other_names.first().needs_review, False)
        mock_send_name_change_notification.assert_not_called()

    @patch("people.models.send_name_change_notification")
    def test_change_name_by_untrusted_user_with_locked_ballots(
        self, mock_send_name_change_notification
    ):
        # Test that a user who is not in the TRUSTED_TO_EDIT_NAME group
        # makes a change to a person's name (who has current, locked ballots),
        # but the change is not saved and the suggested name is flagged for review
        current_election = ElectionFactory(
            election_date="2023-05-05", slug="parl.2023-05-05", current=True
        )
        ballot = BallotPaperFactory(
            election=current_election,
            post=self.dulwich_post,
            ballot_paper_id="parl.foo.2023-05-05",
            candidates_locked=True,
        )

        self.person.memberships.create(
            ballot=ballot,
            post=self.dulwich_post,
            party=self.green_party,
            label="Test Membership",
        )

        response = self.app.get(
            "/person/{}/update".format(self.person.pk), user=self.user
        )

        # check on the name that is currently set
        self.assertEqual(self.person.name, "Tessa Jowell")
        form = response.forms["person-details"]
        form["name"] = "Tessa Palmer"
        # make a change to another field to ensure that change occurs regardless of name change
        form["birth_date"] = 1950
        form["source"] = "Mumsnet"
        form.submit()
        self.person.refresh_from_db()
        # check that the name has not been changed
        self.assertEqual(self.person.name, "Tessa Jowell")
        # check that the name has been added to the other names and needs review
        self.assertEqual(self.person.other_names.first().name, "Tessa Palmer")
        self.assertEqual(self.person.other_names.first().needs_review, True)
        mock_send_name_change_notification.assert_not_called()

    @patch("people.notifications.send_mail")
    @override_settings(SOPN_UPDATE_NOTIFICATION_EMAILS=["fred@example.com"])
    @override_settings(BASE_URL="https://candidates.example.com")
    def test_change_name_by_trusted_user_with_locked_ballots(
        self, mock_send_mail
    ):
        # Test that a user who is in the TRUSTED_TO_EDIT_NAME group
        # makes a change to a person's name,
        # the change is saved directly and an other_name is created,
        # but the other_name is not flagged for review
        # even though they are standing in a locked/current ballot
        self.assertEqual(len(self.person.other_names.all()), 0)
        # get the test user in the TRUSTED_TO_EDIT_NAME group
        self.user = User.objects.get(username="george")

        current_election = ElectionFactory(
            election_date="2023-05-05", slug="parl.2023-05-05", current=True
        )
        ballot = BallotPaperFactory(
            election=current_election,
            post=self.dulwich_post,
            ballot_paper_id="parl.foo.2023-05-05",
            candidates_locked=True,
        )

        self.person.memberships.create(
            ballot=ballot,
            post=self.dulwich_post,
            party=self.green_party,
            label="Test Membership",
        )

        expected_mail_body = textwrap.dedent(
            """\
            Hello,

            The user george changed the name of https://candidates.example.com/person/2009/tessa-palmer from Tessa Jowell to Tessa Palmer.

            This candidate is currently standing in the following ballots:
            - https://candidates.example.com/elections/parl.foo.2023-05-05/
            """
        )

        response = self.app.get(
            "/person/{}/update".format(self.person.pk), user=self.user
        )

        # check on the name that is currently set
        self.assertEqual(self.person.name, "Tessa Jowell")
        form = response.forms["person-details"]
        form["name"] = "Tessa Palmer"
        # make a change to another field to ensure that change occurs regardless of name change
        form["birth_date"] = 1950
        form["source"] = "Mumsnet"
        form.submit()
        self.person.refresh_from_db()
        # check that the name has not been changed
        self.assertEqual(self.person.name, "Tessa Palmer")
        # check an other_names has been created
        self.assertEqual(len(self.person.other_names.all()), 1)
        self.assertEqual(self.person.other_names.first().needs_review, False)
        mock_send_mail.assert_called_once_with(
            "Name for candidate updated",
            expected_mail_body,
            ["fred@example.com"],
        )

    def test_case_change_doesnt_make_other_name(self):
        self.assertEqual(len(self.person.other_names.all()), 0)
        # get the test user in the TRUSTED_TO_EDIT_NAME group
        self.user = User.objects.get(username="george")

        response = self.app.get(
            "/person/{}/update".format(self.person.pk), user=self.user
        )

        # check on the name that is currently set
        self.assertEqual(self.person.name, "Tessa Jowell")
        form = response.forms["person-details"]
        form["name"] = "TeSSa  JoweLL"
        # make a change to another field to ensure that change occurs regardless of name change
        form["source"] = "Mumsnet"
        form.submit()
        self.person.refresh_from_db()
        self.assertEqual(self.person.name, "TeSSa  JoweLL")
        # check an other_names has not been created
        self.assertEqual(len(self.person.other_names.all()), 0)

    def test_edits_prevented(self):
        # See if we get a 403 when submitting a person form
        # for a person who's edits are prevented
        response = self.app.get(
            "/person/{}/update/".format(self.person.pk), user=self.user
        )
        form = response.forms["person-details"]
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
                "biography",
                "favourite_biscuit",
                "delisted",
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

        form = response.forms["person-details"]
        form["favourite_biscuit"] = "Ginger nut"
        form["source"] = "Mumsnet"
        form.submit()

        # Now add to the person's `not_standing` list
        self.person.not_standing.add(self.earlier_election)

        # Now make another edit
        response = self.app.get(
            "/person/{}/update".format(self.person.pk), user=self.user
        )

        form = response.forms["person-details"]
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

        form = response.forms["person-details"]
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

        form = response.forms["person-details"]
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

    def test_change_candidacy_party_updates_party_name(self):
        """
        Regression test to check that when the party on a candidacy is changed
        this also updates the party_name field on the Membership object
        """
        candidacy = self.person.memberships.first()
        self.assertEqual(candidacy.party, self.labour_party)
        self.assertEqual(candidacy.party_name, self.labour_party.name)

        response = self.app.get(
            "/person/{}/update".format(self.person.pk), user=self.user
        )

        form = response.forms["person-details"]
        form["memberships-0-party_identifier_0"].select(self.green_party.ec_id)
        form["memberships-0-party_identifier_1"].value = self.green_party.ec_id
        form["source"] = "http://example.com"
        response = form.submit()

        candidacy = self.person.memberships.first()
        self.assertEqual(candidacy.party, self.green_party)
        self.assertEqual(candidacy.party_name, self.green_party.name)

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

    def test_person_name_edit_does_not_have_spaces_after_saving(self):
        current_election = ElectionFactory(
            election_date="2023-05-05", slug="parl.2023-05-05", current=True
        )
        ballot = BallotPaperFactory(
            election=current_election,
            post=self.dulwich_post,
            ballot_paper_id="parl.foo.2023-05-05",
            candidates_locked=True,
        )

        self.person.memberships.create(
            ballot=ballot,
            post=self.dulwich_post,
            party=self.green_party,
            label="Test Membership",
        )

        response = self.app.get(
            "/person/{}/update".format(self.person.pk), user=self.user
        )

        self.assertEqual(self.person.name, "Tessa Jowell")
        form = response.forms["person-details"]
        form["name"] = " Tessa   Palmer   "
        form["source"] = "Testing spaces are stripped out of person name"
        form.submit()
        self.person.refresh_from_db()
        self.assertEqual(self.person.name, "Tessa Jowell")

    def test_add_candidacy_does_not_update_biography_timestamp(self):
        """Test that the biography (aka statement to voters)
        shows the last updated timestamp and it
        is updated ONLY when the biography is updated
        (it can include other edits). This test
        tries to catch a bug where the timestamp was being updated
        when a candidacy was added to a person."""
        from datetime import timedelta

        timestamp = timezone.now()
        later_timestamp = timestamp + timedelta(hours=8)
        timestamp = timestamp.isoformat()
        later_timestamp = later_timestamp.isoformat()

        # freezegun issue with pandas https://github.com/spulec/freezegun/issues/464
        with freeze_time(timestamp):
            # first, edit an existing person's biography
            biography_update_response = self.app.get(
                "/person/{}/update".format(self.person.pk), user=self.user
            )
            form = biography_update_response.forms["person-details"]
            form["biography"] = "This is a new test biography"
            form["source"] = "Mumsnet"
            form.submit()

            person = Person.objects.with_biography_last_updated().get(
                pk=self.person.pk
            )

            self.assertEqual(len(person.versions), 1)
            person_response_one = self.app.get(
                "/person/{}/".format(person.pk), user=self.user
            )

            biography_update_timestamp = (
                person.biography_last_updated.astimezone()
            )
            # format into a string to compare with the response
            biography_update_timestamp = biography_update_timestamp.strftime(
                "%-d %B %Y %H:%M"
            )
            self.assertContains(
                person_response_one, "This is a new test biography"
            )
            self.assertContains(
                person_response_one,
                "This statement was last updated on {}.".format(
                    biography_update_timestamp
                ),
            )
            # make a second edit adding a candidacy to the same person and assert
            # the biography timestamp has not changed
        with freeze_time(later_timestamp):
            candidacy_update_response = self.app.get(
                "/person/{}/update".format(person.pk), user=self.user
            )
            form = candidacy_update_response.forms["person-details"]
            form["memberships-0-party_identifier_0"].select(
                self.green_party.ec_id
            )
            form[
                "memberships-0-party_identifier_1"
            ].value = self.green_party.ec_id
            form[
                "memberships-0-ballot_paper_id"
            ].value = self.dulwich_post_ballot.ballot_paper_id
            form["memberships-0-party_list_position"] = 1
            form["source"] = "http://example.com"

            form.submit()
            person = Person.objects.with_biography_last_updated().get(
                pk=self.person.pk
            )

            candidacy = person.memberships.first()
            self.assertEqual(candidacy.party, self.green_party)
            self.assertEqual(candidacy.party_name, self.green_party.name)

            candidacy_update_timestamp = (
                person.biography_last_updated.astimezone()
            )
            candidacy_update_timestamp = candidacy_update_timestamp.strftime(
                "%-d %B %Y %H:%M"
            )

            person_response_one = self.app.get(
                "/person/{}/".format(person.pk), user=self.user
            )

            self.assertEqual(len(person.versions), 2)
            self.assertNotEqual(person.biography_last_updated, None)
            # assert that timestamp in the first update and second update are the same
            # because the biography should not have been updated in the second update
            self.assertEqual(
                biography_update_timestamp, candidacy_update_timestamp
            )

            self.assertContains(
                person_response_one,
                "This statement was last updated on {}.".format(
                    biography_update_timestamp
                ),
            )
