from datetime import datetime
from django.urls import reverse
from django_webtest import WebTest
from mock import patch

from candidates.tests.auth import TestUserMixin
from candidates.tests.uk_examples import UK2015ExamplesMixin
from candidates.tests.factories import MembershipFactory
from people.models import Person, PersonIdentifier
from popolo.models import Membership
from uk_results.models import CandidateResult, ResultSet
from utils.testing_utils import deep_sort
from people.tests.factories import PersonFactory

example_timestamp = "2014-09-29T10:11:59.216159"
example_version_id = "5aa6418325c1a0bb"

# FIXME: add a test to check that unauthorized people can't revert


class TestRevertPersonView(TestUserMixin, UK2015ExamplesMixin, WebTest):
    def version_template(self, party_slug):
        return [
            {
                "username": "symroe",
                "information_source": "Just adding example data",
                "ip": "127.0.0.1",
                "version_id": "35ec2d5821176ccc",
                "timestamp": "2014-10-28T14:32:36.835429",
                "data": {
                    "name": "Tessa Jowell",
                    "id": "2009",
                    "twitter_username": "",
                    "candidacies": {
                        "parl.65808.2010-05-06": {"party": party_slug},
                        "parl.65808.2015-05-07": {"party": party_slug},
                    },
                    "homepage_url": "",
                    "birth_date": None,
                    "wikipedia_url": "https://en.wikipedia.org/wiki/Tessa_Jowell",
                    "identifiers": [
                        {
                            "identifier": "uk.org.publicwhip/person/10326",
                            "scheme": "uk.org.publicwhip",
                        }
                    ],
                    "email": "jowell@example.com",
                    "extra_fields": {},
                },
            },
            {
                "username": "mark",
                "information_source": "An initial version",
                "ip": "127.0.0.1",
                "version_id": "5469de7db0cbd155",
                "timestamp": "2014-10-01T15:12:34.732426",
                "data": {
                    "name": "Tessa Jowell",
                    "other_names": [
                        {
                            "name": "Tessa Palmer",
                            "note": "maiden name",
                            "start_date": None,
                            "end_date": None,
                        }
                    ],
                    "id": "2009",
                    "twitter_username": "",
                    "candidacies": {
                        "parl.65808.2010-05-06": {"party": party_slug}
                    },
                    "homepage_url": "http://example.org/tessajowell",
                    "birth_date": "1947",
                    "biography": "",
                    "wikipedia_url": "",
                    "identifiers": [
                        {
                            "identifier": "uk.org.publicwhip/person/10326",
                            "scheme": "uk.org.publicwhip",
                        }
                    ],
                    "email": "tessa.jowell@example.com",
                    "extra_fields": {},
                },
            },
        ]

    def setUp(self):
        super().setUp()
        person = PersonFactory.create(
            id=2009,
            name="Tessa Jowell",
            versions=self.version_template(party_slug=self.labour_party.ec_id),
        )
        PersonIdentifier.objects.create(
            person=person, value="jowell@example.com", value_type="email"
        )
        PersonIdentifier.objects.create(
            person=person,
            internal_identifier="10326",
            value_type="theyworkforyou",
        )
        MembershipFactory.create(
            person=person,
            post=self.dulwich_post,
            party=self.labour_party,
            ballot=self.dulwich_post_ballot,
        )
        MembershipFactory.create(
            person=person,
            post=self.dulwich_post,
            party=self.labour_party,
            ballot=self.dulwich_post_ballot_earlier,
        )

    @patch("candidates.views.version_data.get_current_timestamp")
    @patch("candidates.views.version_data.create_version_id")
    def test_revert_to_earlier_version(
        self, mock_create_version_id, mock_get_current_timestamp
    ):
        mock_get_current_timestamp.return_value = example_timestamp
        mock_create_version_id.return_value = example_version_id

        response = self.app.get("/person/2009/update", user=self.user)
        revert_form = response.forms["revert-form-5469de7db0cbd155"]
        revert_form[
            "source"
        ] = "Reverting to version 5469de7db0cbd155 for testing purposes"
        response = revert_form.submit()
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.location, "/person/2009")

        # Now get the person from the database and check if the
        # details are the same as the earlier version:
        person = Person.objects.get(id=2009)

        # First check that a new version has been created:
        new_versions = person.versions

        self.maxDiff = None
        expected_new_version = {
            "data": {
                "blog_url": "",
                "facebook_page_url": "",
                "facebook_personal_url": "",
                "name": "Tessa Jowell",
                "honorific_suffix": "",
                "party_ppc_page_url": "",
                "gender": "",
                "instagram_url": "",
                "linkedin_url": "",
                "mastodon_username": "",
                "id": "2009",
                "other_names": [
                    {
                        "name": "Tessa Palmer",
                        "note": "maiden name",
                        "end_date": None,
                        "start_date": None,
                    }
                ],
                "honorific_prefix": "",
                "candidacies": {
                    "parl.65808.2010-05-06": {"party": self.labour_party.ec_id}
                },
                "homepage_url": "http://example.org/tessajowell",
                "twitter_username": "",
                "wikipedia_url": "",
                "youtube_profile": "",
                "wikidata_id": "",
                "birth_date": "1947",
                "death_date": "",
                "biography": "",
                "identifiers": [
                    {
                        "identifier": "uk.org.publicwhip/person/10326",
                        "scheme": "uk.org.publicwhip",
                    }
                ],
                "email": "tessa.jowell@example.com",
                "extra_fields": {"favourite_biscuits": ""},
            },
            "information_source": "Reverting to version 5469de7db0cbd155 for testing purposes",
            "timestamp": "2014-09-29T10:11:59.216159",
            "username": "john",
            "version_id": "5aa6418325c1a0bb",
        }

        self.assertDictEqual(
            deep_sort(new_versions[0]), deep_sort(expected_new_version)
        )

        self.assertEqual(person.birth_date, "1947")
        self.assertEqual(
            person.get_single_identifier_value("homepage_url"),
            "http://example.org/tessajowell",
        )

        candidacies = Membership.objects.filter(person=person).order_by(
            "ballot__election__election_date"
        )

        self.assertEqual(len(candidacies), 1)
        self.assertEqual(candidacies[0].ballot.election.slug, "parl.2010-05-06")

        # The homepage link should have been added and the Wikipedia
        # one removed, and the theyworkforyou ID created:
        self.assertEqual(3, person.tmp_person_identifiers.all().count())
        self.assertIsNone(person.get_single_identifier_value("wikipedia_url"))

    @patch("candidates.views.version_data.get_current_timestamp")
    @patch("candidates.views.version_data.create_version_id")
    def test_revert_to_earlier_version_with_results(
        self, mock_create_version_id, mock_get_current_timestamp
    ):
        mock_get_current_timestamp.return_value = example_timestamp
        mock_create_version_id.return_value = example_version_id

        result_set = ResultSet.objects.create(
            ballot=self.dulwich_post_ballot_earlier,
            num_turnout_reported=51561,
            num_spoilt_ballots=42,
            ip_address="127.0.0.1",
        )
        CandidateResult.objects.create(
            result_set=result_set,
            membership=Person.objects.get(pk=2009).memberships.first(),
            num_ballots=32614,
        )

        response = self.app.get("/person/2009/update", user=self.user)
        revert_form = response.forms["revert-form-5469de7db0cbd155"]
        revert_form[
            "source"
        ] = "Reverting to version 5469de7db0cbd155 for testing purposes"
        response = revert_form.submit()
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.location, "/person/2009")

        # Now get the person from the database and check if the
        # details are the same as the earlier version:
        person = Person.objects.get(id=2009)
        self.assertTrue(
            Membership.objects.filter(person_id=person.pk).count(), 2
        )
        self.assertTrue(
            CandidateResult.objects.filter(
                membership__person_id=person.pk
            ).exists()
        )

    def test_revert_with_memberships(self):
        person = Person.objects.get(id=2009)
        self.dulwich_post_ballot.candidates_locked = True
        self.dulwich_post_ballot.save()
        self.dulwich_post_ballot_earlier.candidates_locked = True
        self.dulwich_post_ballot_earlier.save()

        response = self.app.get(person.get_edit_url(), user=self.user)
        form = response.forms[1]
        form["source"] = "made up"
        form.submit()

        response = self.app.get(person.get_edit_url(), user=self.user)
        revert_form = response.forms["revert-form-5469de7db0cbd155"]
        revert_form[
            "source"
        ] = "Reverting to version 5469de7db0cbd155 for testing purposes"
        response = revert_form.submit()

    def test_revert_with_memberships_previous_party_affiliations(self):
        person = PersonFactory()
        membership = MembershipFactory.create(
            person=person, ballot=self.senedd_ballot, party=self.ld_party
        )
        membership.previous_party_affiliations.add(self.conservative_party)
        # create an initial version
        person.record_version(
            change_metadata={
                "information_source": "initial version",
                "version_id": "1",
                "timestamp": datetime.utcnow().isoformat(),
                "username": self.user.username,
            }
        )
        person.save()
        self.assertEqual(membership.previous_party_affiliations.count(), 1)

        # make a change and record the version
        membership.previous_party_affiliations.clear()
        person.record_version(
            change_metadata={
                "information_source": "cleared the previous_party_affiliations",
                "version_id": "2",
                "timestamp": datetime.utcnow().isoformat(),
                "username": self.user.username,
            }
        )
        person.save()
        self.assertEqual(membership.previous_party_affiliations.count(), 0)

        # revert to the earlier version
        self.client.force_login(self.user)
        url = reverse("person-revert", kwargs={"person_id": person.pk})
        response = self.client.post(
            url, data={"version_id": "1", "source": "Testing"}, follow=True
        )
        self.assertEqual(response.status_code, 200)
        with self.assertRaises(Membership.DoesNotExist):
            membership.refresh_from_db()
        new_membership = person.memberships.get()
        self.assertEqual(new_membership.previous_party_affiliations.count(), 1)
