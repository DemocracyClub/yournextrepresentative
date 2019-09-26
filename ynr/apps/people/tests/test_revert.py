import json
from string import Template

from django.db.models import F
from django_webtest import WebTest
from mock import patch

import people.tests.factories
from candidates.tests import factories
from candidates.tests.auth import TestUserMixin
from candidates.tests.uk_examples import UK2015ExamplesMixin
from compat import deep_sort
from people.models import Person, PersonIdentifier
from popolo.models import Membership

example_timestamp = "2014-09-29T10:11:59.216159"
example_version_id = "5aa6418325c1a0bb"

# FIXME: add a test to check that unauthorized people can't revert


class TestRevertPersonView(TestUserMixin, UK2015ExamplesMixin, WebTest):

    version_template = Template(
        """[
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
              "standing_in": {
                "parl.2010-05-06": {
                  "post_id": "65808",
                  "name": "Dulwich and West Norwood",
                  "mapit_url": "http://mapit.mysociety.org/area/65808"
                },
                "parl.2015-05-07": {
                  "post_id": "65808",
                  "name": "Dulwich and West Norwood",
                  "mapit_url": "http://mapit.mysociety.org/area/65808"
                }
              },
              "homepage_url": "",
              "birth_date": null,
              "wikipedia_url": "https://en.wikipedia.org/wiki/Tessa_Jowell",
              "party_memberships": {
                "parl.2010-05-06": {
                  "id": "$slug",
                  "name": "Labour Party"
                },
                "parl.2015-05-07": {
                  "id": "$slug",
                  "name": "Labour Party"
                }
              },
              "identifiers": [
                {
                  "identifier": "uk.org.publicwhip/person/10326",
                  "scheme": "uk.org.publicwhip"
                }
              ],
              "email": "jowell@example.com",
              "extra_fields": {}
            }
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
                  "start_date": null,
                  "end_date": null
                }
              ],
              "id": "2009",
              "twitter_username": "",
              "standing_in": {
                "parl.2010-05-06": {
                  "post_id": "65808",
                  "name": "Dulwich and West Norwood",
                  "mapit_url": "http://mapit.mysociety.org/area/65808"
                }
              },
              "homepage_url": "http://example.org/tessajowell",
              "birth_date": "1947-09-17",
              "biography": "",
              "wikipedia_url": "",
              "party_memberships": {
                "parl.2010-05-06": {
                  "id": "$slug",
                  "name": "Labour Party"
                }
              },
              "identifiers": [
                {
                  "identifier": "uk.org.publicwhip/person/10326",
                  "scheme": "uk.org.publicwhip"
                }
              ],
              "email": "tessa.jowell@example.com",
              "extra_fields": {}
            }
          }
        ]
    """
    )

    def setUp(self):
        super().setUp()
        person = people.tests.factories.PersonFactory.create(
            id=2009,
            name="Tessa Jowell",
            versions=self.version_template.substitute(
                slug=self.labour_party.legacy_slug
            ),
        )
        PersonIdentifier.objects.create(
            person=person, value="jowell@example.com", value_type="email"
        )
        PersonIdentifier.objects.create(
            person=person,
            internal_identifier="10326",
            value_type="theyworkforyou",
        )
        factories.MembershipFactory.create(
            person=person,
            post=self.dulwich_post,
            party=self.labour_party,
            ballot=self.dulwich_post_ballot,
        )
        factories.MembershipFactory.create(
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
        new_versions = json.loads(person.versions)

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
                "standing_in": {
                    "parl.2010-05-06": {
                        "post_id": "65808",
                        "name": "Dulwich and West Norwood",
                    }
                },
                "homepage_url": "http://example.org/tessajowell",
                "twitter_username": "",
                "wikipedia_url": "",
                "youtube_profile": "",
                "wikidata_id": "",
                "party_memberships": {
                    "parl.2010-05-06": {
                        "id": self.labour_party.legacy_slug,
                        "name": "Labour Party",
                    }
                },
                "birth_date": "1947-09-17",
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

        self.assertEqual(person.birth_date, "1947-09-17")
        self.assertEqual(
            person.get_single_identifier_value("homepage_url"),
            "http://example.org/tessajowell",
        )

        candidacies = Membership.objects.filter(
            person=person, role=F("ballot__election__candidate_membership_role")
        ).order_by("ballot__election__election_date")

        self.assertEqual(len(candidacies), 1)
        self.assertEqual(candidacies[0].ballot.election.slug, "parl.2010-05-06")

        # The homepage link should have been added and the Wikipedia
        # one removed, and the theyworkforyou ID created:
        self.assertEqual(3, person.tmp_person_identifiers.all().count())
        self.assertIsNone(person.get_single_identifier_value("wikipedia_url"))
