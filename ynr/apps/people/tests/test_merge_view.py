from os.path import join, dirname, realpath
from shutil import rmtree

from mock import patch

from django.conf import settings
from django.db.models import F
from django.test.utils import override_settings

from django_webtest import WebTest

import people.tests.factories
from popolo.models import Membership

from candidates.models import PersonRedirect, LoggedAction
from candidates.models.versions import revert_person_from_version_data
from people.models import PersonImage, Person
from ynr.helpers import mkdir_p
from candidates.tests.auth import TestUserMixin
from candidates.tests.uk_examples import UK2015ExamplesMixin
from candidates.tests import factories
from ynr.helpers import mkdir_p
from moderation_queue.tests.paths import EXAMPLE_IMAGE_FILENAME

example_timestamp = "2014-09-29T10:11:59.216159"
example_version_id = "5aa6418325c1a0bb"

TEST_MEDIA_ROOT = realpath(join(dirname(__file__), "media"))


@override_settings(MEDIA_ROOT=TEST_MEDIA_ROOT)
@override_settings(TWITTER_APP_ONLY_BEARER_TOKEN=None)
class TestMergePeopleView(TestUserMixin, UK2015ExamplesMixin, WebTest):
    def setUp(self):
        super().setUp()
        mkdir_p(TEST_MEDIA_ROOT)
        # Create Tessa Jowell (the primary person)
        person = people.tests.factories.PersonFactory.create(
            id=2009,
            name="Tessa Jowell",
            gender="female",
            honorific_suffix="DBE",
            email="jowell@example.com",
            versions="""
                [
                  {
                    "username": "symroe",
                    "information_source": "Just adding example data",
                    "ip": "127.0.0.1",
                    "version_id": "35ec2d5821176ccc",
                    "timestamp": "2014-10-28T14:32:36.835429",
                    "data": {
                      "name": "Tessa Jowell",
                      "other_names": [
                        {
                          "name": "Tessa Palmer",
                          "note": "maiden name"
                        }
                      ],
                      "id": "2009",
                      "honorific_suffix": "DBE",
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
                      "gender": "female",
                      "homepage_url": "",
                      "birth_date": null,
                      "wikipedia_url": "https://en.wikipedia.org/wiki/Tessa_Jowell",
                      "party_memberships": {
                        "parl.2010-05-06": {
                          "id": "party:53",
                          "name": "Labour Party"
                        },
                        "parl.2015-05-07": {
                          "id": "party:53",
                          "name": "Labour Party"
                        }
                      },
                      "email": "jowell@example.com"
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
                      "wikipedia_url": "",
                      "party_memberships": {
                        "parl.2010-05-06": {
                          "id": "party:53",
                          "name": "Labour Party"
                        }
                      },
                      "email": "tessa.jowell@example.com"
                    }
                  }
                ]
            """,
        )
        PersonImage.objects.create_from_file(
            EXAMPLE_IMAGE_FILENAME,
            "images/jowell-pilot.jpg",
            defaults={
                "person": person,
                "is_primary": True,
                "source": "Taken from Wikipedia",
                "copyright": "example-license",
                "uploading_user": self.user,
                "user_notes": "A photo of Tessa Jowell",
            },
        )
        factories.MembershipFactory.create(
            person=person,
            post=self.local_post,
            party=self.labour_party,
            post_election=self.local_pee,
        )
        factories.MembershipFactory.create(
            person=person,
            post=self.dulwich_post,
            party=self.labour_party,
            post_election=self.dulwich_post_pee_earlier,
        )
        # Now create Shane Collins (who we'll merge into Tessa Jowell)
        person = people.tests.factories.PersonFactory.create(
            id=2007,
            name="Shane Collins",
            gender="male",
            honorific_prefix="Mr",
            email="shane@gn.apc.org",
            versions="""
                [
                  {
                    "data": {
                      "birth_date": null,
                      "email": "shane@gn.apc.org",
                      "facebook_page_url": "",
                      "facebook_personal_url": "",
                      "gender": "male",
                      "homepage_url": "",
                      "honorific_prefix": "Mr",
                      "honorific_suffix": "",
                      "id": "2007",
                      "identifiers": [],
                      "image": null,
                      "linkedin_url": "",
                      "name": "Shane Collins",
                      "other_names": [],
                      "party_memberships": {
                        "parl.2010-05-06": {
                          "id": "party:63",
                          "name": "Green Party"
                        }
                      },
                      "party_ppc_page_url": "",
                      "proxy_image": null,
                      "standing_in": {
                        "parl.2010-05-06": {
                          "mapit_url": "http://mapit.mysociety.org/area/65808",
                          "name": "Dulwich and West Norwood",
                          "post_id": "65808"
                        },
                        "2015": null
                      },
                      "twitter_username": "",
                      "wikipedia_url": ""
                    },
                    "information_source": "http://www.lambeth.gov.uk/sites/default/files/ec-dulwich-and-west-norwood-candidates-and-notice-of-poll-2015.pdf",
                    "timestamp": "2015-04-09T20:32:09.237610",
                    "username": "JPCarrington",
                    "version_id": "274e50504df330e4"
                  },
                  {
                    "data": {
                      "birth_date": null,
                      "email": "shane@gn.apc.org",
                      "facebook_page_url": null,
                      "facebook_personal_url": null,
                      "gender": "male",
                      "homepage_url": null,
                      "id": "2007",
                      "identifiers": [],
                      "name": "Shane Collins",
                      "party_memberships": {
                        "parl.2010-05-06": {
                          "id": "party:63",
                          "name": "Green Party"
                        }
                      },
                      "party_ppc_page_url": null,
                      "phone": "07939 196612",
                      "slug": "shane-collins",
                      "standing_in": {
                        "parl.2010-05-06": {
                          "mapit_url": "http://mapit.mysociety.org/area/65808",
                          "name": "Dulwich and West Norwood",
                          "post_id": "65808"
                        }
                      },
                      "twitter_username": null,
                      "wikipedia_url": null
                    },
                    "information_source": "Imported from YourNextMP data from 2010",
                    "timestamp": "2014-11-21T18:16:47.670167",
                    "username": "JPCarrington",
                    "version_id": "68a452284d95d9ab"
                  }
                ]
            """,
        )
        PersonImage.objects.create_from_file(
            EXAMPLE_IMAGE_FILENAME,
            "images/collins-pilot.jpg",
            defaults={
                "person": person,
                "is_primary": True,
                "source": "Taken from Twitter",
                "copyright": "profile-photo",
                "uploading_user": self.user,
                "user_notes": "A photo of Shane Collins",
            },
        )
        factories.MembershipFactory.create(
            person=person,
            post=self.dulwich_post,
            party=self.green_party,
            post_election=self.dulwich_post_pee_earlier,
        )
        factories.MembershipFactory.create(
            person=person,
            post=self.dulwich_post,
            party=self.green_party,
            post_election=self.edinburgh_east_post_pee,
        )

    def tearDown(self):
        # Delete the images we created in the test media root:
        rmtree(TEST_MEDIA_ROOT)

    def test_merge_disallowed_no_form(self):
        response = self.app.get("/person/2009/update", user=self.user)
        self.assertNotIn("person-merge", response.forms)

    def test_merge_two_people_disallowed(self):
        # Get the update page for the person just to get the CSRF token:
        response = self.app.get("/person/2009/update", user=self.user)
        csrftoken = self.app.cookies["csrftoken"]
        response = self.app.post(
            "/person/2009/merge",
            params={"csrfmiddlewaretoken": csrftoken, "other": "2007"},
            expect_errors=True,
        )
        self.assertEqual(response.status_code, 403)

    @patch("candidates.views.version_data.get_current_timestamp")
    @patch("candidates.views.version_data.create_version_id")
    def test_merge_two_people(
        self, mock_create_version_id, mock_get_current_timestamp
    ):
        mock_get_current_timestamp.return_value = example_timestamp
        mock_create_version_id.return_value = example_version_id

        primary_person = Person.objects.get(pk=2009)
        non_primary_person = Person.objects.get(pk=2007)
        self.assertEqual(Membership.objects.count(), 4)
        response = self.app.get(
            "/person/2009/update", user=self.user_who_can_merge
        )
        merge_form = response.forms["person-merge"]
        merge_form["other"] = "2007"
        response = merge_form.submit()

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.location, "/person/2009/tessa-jowell")

        # Check that the redirect object has been made:
        self.assertEqual(
            PersonRedirect.objects.filter(
                old_person_id=2009, new_person_id=2007
            ).count(),
            1,
        )

        # Check that person 2007 redirects to person 2009 in future
        response = self.app.get("/person/2009")
        self.assertEqual(response.status_code, 301)

        # Check that the other person was deleted (in the future we
        # might want to "soft delete" the person instead).
        self.assertEqual(Person.objects.filter(id=2009).count(), 0)

        # Get the merged person, and check that everything's as we expect:
        merged_person = Person.objects.get(id=2007)

        self.assertEqual(merged_person.birth_date, "")
        self.assertEqual(merged_person.email, "shane@gn.apc.org")
        self.assertEqual(merged_person.gender, "female")
        self.assertEqual(merged_person.honorific_prefix, "Mr")
        self.assertEqual(merged_person.honorific_suffix, "DBE")

        candidacies = Membership.objects.filter(person=merged_person)
        self.assertEqual(len(candidacies), 3)
        expected_ballots = {
            "parl.65808.2010-05-06",
            "parl.14419.2015-05-07",
            "local.maidstone.DIW:E05005004.2016-05-05",
        }
        found_ballots = {
            mem.post_election.ballot_paper_id for mem in candidacies
        }
        self.assertEqual(expected_ballots, found_ballots)

        # Check that there are only two Membership objects
        self.assertEqual(
            3, Membership.objects.filter(person=merged_person).count()
        )

        other_names = list(merged_person.other_names.all())
        self.assertEqual(len(other_names), 1)
        self.assertEqual(other_names[0].name, "Tessa Jowell")

        # Check that the remaining person now has two images, i.e. the
        # one from the person to delete is added to the existing images:
        self.assertEqual(2, merged_person.images.count())

        primary_image = merged_person.images.get(is_primary=True)
        non_primary_image = merged_person.images.get(is_primary=False)

        self.assertEqual(primary_image.user_notes, "A photo of Tessa Jowell")
        self.assertEqual(
            non_primary_image.user_notes, "A photo of Shane Collins"
        )

    @patch("candidates.views.version_data.get_current_timestamp")
    @patch("candidates.views.version_data.create_version_id")
    def test_merge_regression(
        self, mock_create_version_id, mock_get_current_timestamp
    ):
        mock_get_current_timestamp.return_value = example_timestamp
        mock_create_version_id.return_value = example_version_id

        # Create the primary and secondary versions of Stuart Jeffrey
        # that failed from their JSON serialization.
        stuart_primary = people.tests.factories.PersonFactory.create(
            id="2111", name="Stuart Jeffrey"
        )
        stuart_secondary = people.tests.factories.PersonFactory.create(
            id="12207", name="Stuart Robert Jeffrey"
        )

        # And create the two Westminster posts:
        factories.PostFactory.create(
            elections=(self.election, self.earlier_election),
            slug="65878",
            label="Canterbury",
            party_set=self.gb_parties,
            organization=self.commons,
        )
        factories.PostFactory.create(
            elections=(self.election, self.earlier_election),
            slug="65936",
            label="Maidstone and The Weald",
            party_set=self.gb_parties,
            organization=self.commons,
        )

        # Update each of them from the versions that were merged, and merged badly:
        revert_person_from_version_data(
            stuart_primary,
            {
                "birth_date": "1967-12-22",
                "email": "sjeffery@fmail.co.uk",
                "facebook_page_url": "",
                "facebook_personal_url": "",
                "gender": "male",
                "homepage_url": "http://www.stuartjeffery.net/",
                "honorific_prefix": "",
                "honorific_suffix": "",
                "id": "2111",
                "identifiers": [
                    {"identifier": "15712527", "scheme": "twitter"}
                ],
                "image": "http://yournextmp.popit.mysociety.org/persons/2111/image/54bc790ecb19ebca71e2af8e",
                "linkedin_url": "",
                "name": "Stuart Jeffery",
                "other_names": [],
                "party_memberships": {
                    "parl.2010-05-06": {
                        "id": "party:63",
                        "name": "Green Party",
                    },
                    "parl.2015-05-07": {
                        "id": "party:63",
                        "name": "Green Party",
                    },
                },
                "party_ppc_page_url": "https://my.greenparty.org.uk/candidates/105873",
                "standing_in": {
                    "parl.2010-05-06": {
                        "name": "Maidstone and The Weald",
                        "post_id": "65936",
                    },
                    "parl.2015-05-07": {
                        "elected": False,
                        "name": "Canterbury",
                        "post_id": "65878",
                    },
                },
                "twitter_username": "stuartjeffery",
                "wikipedia_url": "",
            },
        )

        revert_person_from_version_data(
            stuart_secondary,
            {
                "birth_date": "",
                "email": "",
                "facebook_page_url": "",
                "facebook_personal_url": "",
                "gender": "",
                "homepage_url": "",
                "honorific_prefix": "",
                "honorific_suffix": "",
                "id": "12207",
                "image": None,
                "linkedin_url": "",
                "name": "Stuart Robert Jeffery",
                "other_names": [],
                "party_memberships": {
                    "local.maidstone.2016-05-05": {
                        "id": "party:63",
                        "name": "Green Party",
                    }
                },
                "party_ppc_page_url": "",
                "standing_in": {
                    "local.maidstone.2016-05-05": {
                        "elected": False,
                        "name": "Shepway South ward",
                        "post_id": "DIW:E05005004",
                    }
                },
                "twitter_username": "",
                "wikipedia_url": "",
            },
        )

        response = self.app.get(
            "/person/2111/update", user=self.user_who_can_merge
        )
        merge_form = response.forms["person-merge"]
        merge_form["other"] = "12207"
        response = merge_form.submit()

        self.assertEqual(response.status_code, 302)
        self.assertEqual(
            response.location, "/person/2111/stuart-robert-jeffery"
        )

        merged_person = Person.objects.get(pk="2111")

        candidacies = (
            Membership.objects.filter(
                person=merged_person,
                role=F("post_election__election__candidate_membership_role"),
            )
            .values_list(
                "post_election__election__slug",
                "post__slug",
                "party__legacy_slug",
            )
            .order_by("post_election__election__slug")
        )

        self.assertEqual(
            list(candidacies),
            [
                ("local.maidstone.2016-05-05", "DIW:E05005004", "party:63"),
                ("parl.2010-05-06", "65936", "party:63"),
                ("parl.2015-05-07", "65878", "party:63"),
            ],
        )

    def test_merge_logged_actions(self):
        """
        Regression test for https://github.com/DemocracyClub/yournextrepresentative/issues/758:

        > User Apexharper made four edits to two separate candidate pages at
        > around 7am on 20 Jan - all four edits were appearing in
        > /recent-changes.

        > I then merged 46170 into 49291 and now only the two edits to the
        > latter page are listed
        """
        self.assertFalse(LoggedAction.objects.exists())
        primary_person = Person.objects.get(pk=2009)
        non_primary_person = Person.objects.get(pk=2007)

        def _do_edit_for_user(person, field, value, source):
            response = self.app.get(
                "/person/{}/update".format(person.pk), user=self.user
            )
            form = response.forms[1]
            form[field] = value
            form["source"] = source
            form.submit()

        _do_edit_for_user(
            primary_person, "favourite_biscuit", "Ginger nut", "Mumsnet"
        )
        _do_edit_for_user(
            primary_person,
            "biography",
            "Now, this is a story all about how",
            "West Philadelphia",
        )
        _do_edit_for_user(
            non_primary_person,
            "biography",
            "I've lived here for ages",
            "Bel Air",
        )
        _do_edit_for_user(
            non_primary_person, "birth_date", "1968-09-25", "Wikipedia"
        )

        self.assertEqual(LoggedAction.objects.count(), 4)
        self.assertEqual(Person.objects.count(), 2)
        response = self.app.get("/recent-changes")
        self.assertEqual(len(response.context["actions"].object_list), 4)

        response = self.app.get(
            "/person/{}/update".format(primary_person.pk),
            user=self.user_who_can_merge,
        )
        merge_form = response.forms["person-merge"]
        merge_form["other"] = non_primary_person.pk
        response = merge_form.submit()

        self.assertEqual(Person.objects.count(), 1)
        # 5 actions, because we create a "merge" logged action
        self.assertEqual(LoggedAction.objects.count(), 5)
        response = self.app.get("/recent-changes")
        self.assertEqual(len(response.context["actions"].object_list), 5)
