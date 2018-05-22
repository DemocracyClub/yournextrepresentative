from __future__ import unicode_literals

from os.path import join, dirname, realpath
from shutil import rmtree

from mock import patch

from django.conf import settings
from django.db.models import F
from django.test.utils import override_settings

from django_webtest import WebTest

from popolo.models import Membership, Person

from candidates.models import PersonRedirect, MembershipExtra, ImageExtra
from candidates.models.versions import revert_person_from_version_data
from ynr.helpers import mkdir_p
from .auth import TestUserMixin
from .uk_examples import UK2015ExamplesMixin
from . import factories
from ynr.helpers import mkdir_p
from moderation_queue.tests.paths import EXAMPLE_IMAGE_FILENAME

example_timestamp = '2014-09-29T10:11:59.216159'
example_version_id = '5aa6418325c1a0bb'

TEST_MEDIA_ROOT = realpath(join(dirname(__file__), 'media'))

@override_settings(MEDIA_ROOT=TEST_MEDIA_ROOT)
@override_settings(TWITTER_APP_ONLY_BEARER_TOKEN=None)
@patch('candidates.views.people.additional_merge_actions')
class TestMergePeopleView(TestUserMixin, UK2015ExamplesMixin, WebTest):

    def setUp(self):
        super(TestMergePeopleView, self).setUp()
        mkdir_p(TEST_MEDIA_ROOT)
        # Create Tessa Jowell (the primary person)
        person_extra = factories.PersonExtraFactory.create(
            base__id=2009,
            base__name='Tessa Jowell',
            base__gender='female',
            base__honorific_suffix='DBE',
            base__email='jowell@example.com',
            versions='''
                [
                  {
                    "username": "symroe",
                    "information_source": "Just adding example data",
                    "ip": "127.0.0.1",
                    "version_id": "35ec2d5821176ccc",
                    "timestamp": "2014-10-28T14:32:36.835429",
                    "data": {
                      "name": "Tessa Jowell",
                      "id": "2009",
                      "honorific_suffix": "DBE",
                      "twitter_username": "",
                      "standing_in": {
                        "2010": {
                          "post_id": "65808",
                          "name": "Dulwich and West Norwood",
                          "mapit_url": "http://mapit.mysociety.org/area/65808"
                        },
                        "2015": {
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
                        "2010": {
                          "id": "party:53",
                          "name": "Labour Party"
                        },
                        "2015": {
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
                        "2010": {
                          "post_id": "65808",
                          "name": "Dulwich and West Norwood",
                          "mapit_url": "http://mapit.mysociety.org/area/65808"
                        }
                      },
                      "homepage_url": "http://example.org/tessajowell",
                      "birth_date": "1947-09-17",
                      "wikipedia_url": "",
                      "party_memberships": {
                        "2010": {
                          "id": "party:53",
                          "name": "Labour Party"
                        }
                      },
                      "email": "tessa.jowell@example.com"
                    }
                  }
                ]
            ''',
        )
        ImageExtra.objects.create_from_file(
            EXAMPLE_IMAGE_FILENAME,
            'images/jowell-pilot.jpg',
            base_kwargs={
                'content_object': person_extra,
                'is_primary': True,
                'source': 'Taken from Wikipedia',
            },
            extra_kwargs={
                'copyright': 'example-license',
                'uploading_user': self.user,
                'user_notes': 'A photo of Tessa Jowell',
            },
        )
        factories.CandidacyExtraFactory.create(
            base__person=person_extra.base,
            base__post=self.dulwich_post_extra.base,
            base__on_behalf_of=self.labour_party_extra.base,
            post_election=self.dulwich_post_extra_pee,
        )
        factories.CandidacyExtraFactory.create(
            base__person=person_extra.base,
            base__post=self.dulwich_post_extra.base,
            base__on_behalf_of=self.labour_party_extra.base,
            post_election=self.dulwich_post_extra_pee_earlier,
        )
        # Now create Shane Collins (who we'll merge into Tessa Jowell)
        person_extra = factories.PersonExtraFactory.create(
            base__id=2007,
            base__name='Shane Collins',
            base__gender='male',
            base__honorific_prefix='Mr',
            base__email='shane@gn.apc.org',
            versions='''
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
                      "identifiers": [
                        {
                          "id": "547786cc737edc5252ce5af1",
                          "identifier": "2961",
                          "scheme": "yournextmp-candidate"
                        }
                      ],
                      "image": null,
                      "linkedin_url": "",
                      "name": "Shane Collins",
                      "other_names": [],
                      "party_memberships": {
                        "2010": {
                          "id": "party:63",
                          "name": "Green Party"
                        }
                      },
                      "party_ppc_page_url": "",
                      "proxy_image": null,
                      "standing_in": {
                        "2010": {
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
                      "identifiers": [
                        {
                          "identifier": "2961",
                          "scheme": "yournextmp-candidate"
                        }
                      ],
                      "name": "Shane Collins",
                      "party_memberships": {
                        "2010": {
                          "id": "party:63",
                          "name": "Green Party"
                        }
                      },
                      "party_ppc_page_url": null,
                      "phone": "07939 196612",
                      "slug": "shane-collins",
                      "standing_in": {
                        "2010": {
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
                    "version_id": "68a452284d95d9ab"
                  }
                ]
            ''')
        ImageExtra.objects.create_from_file(
            EXAMPLE_IMAGE_FILENAME,
            'images/collins-pilot.jpg',
            base_kwargs={
                'content_object': person_extra,
                'is_primary': True,
                'source': 'Taken from Twitter',
            },
            extra_kwargs={
                'copyright': 'profile-photo',
                'uploading_user': self.user,
                'user_notes': 'A photo of Shane Collins',
            },
        )
        factories.CandidacyExtraFactory.create(
            base__person=person_extra.base,
            base__post=self.dulwich_post_extra.base,
            base__on_behalf_of=self.green_party_extra.base,
            post_election=self.dulwich_post_extra_pee,
        )
        factories.CandidacyExtraFactory.create(
            base__person=person_extra.base,
            base__post=self.dulwich_post_extra.base,
            base__on_behalf_of=self.green_party_extra.base,
            post_election=self.dulwich_post_extra_pee,
        )

    def tearDown(self):
        # Delete the images we created in the test media root:
        rmtree(TEST_MEDIA_ROOT)

    def test_merge_disallowed_no_form(self, mock_additional_merge_actions):
        response = self.app.get('/person/2009/update', user=self.user)
        self.assertNotIn('person-merge', response.forms)
        self.assertEqual(mock_additional_merge_actions.call_count, 0)

    def test_merge_two_people_disallowed(self, mock_additional_merge_actions):
        # Get the update page for the person just to get the CSRF token:
        response = self.app.get('/person/2009/update', user=self.user)
        csrftoken = self.app.cookies['csrftoken']
        response = self.app.post(
            '/person/2009/merge',
            {
                'csrfmiddlewaretoken': csrftoken,
                'other': '2007',
            },
            expect_errors=True
        )
        self.assertEqual(response.status_code, 403)
        self.assertEqual(mock_additional_merge_actions.call_count, 0)

    @patch('candidates.views.version_data.get_current_timestamp')
    @patch('candidates.views.version_data.create_version_id')
    def test_merge_two_people(
            self,
            mock_create_version_id,
            mock_get_current_timestamp,
            mock_additional_merge_actions,
    ):
        mock_get_current_timestamp.return_value = example_timestamp
        mock_create_version_id.return_value = example_version_id

        primary_person = Person.objects.get(pk=2009)
        non_primary_person = Person.objects.get(pk=2007)

        response = self.app.get('/person/2009/update', user=self.user_who_can_merge)
        merge_form = response.forms['person-merge']
        merge_form['other'] = '2007'
        response = merge_form.submit()

        self.assertEqual(response.status_code, 302)
        self.assertEqual(
            response.location,
            '/person/2009/tessa-jowell'
        )

        # Check that the redirect object has been made:
        self.assertEqual(
            PersonRedirect.objects.filter(
                old_person_id=2007,
                new_person_id=2009,
            ).count(),
            1
        )

        # Check that person 2007 redirects to person 2009 in future
        response = self.app.get('/person/2007')
        self.assertEqual(response.status_code, 301)


        # Check that the other person was deleted (in the future we
        # might want to "soft delete" the person instead).
        self.assertEqual(Person.objects.filter(id=2007).count(), 0)

        # Get the merged person, and check that everything's as we expect:
        merged_person = Person.objects.get(id=2009)

        self.assertEqual(merged_person.birth_date, '')
        self.assertEqual(merged_person.email, 'jowell@example.com')
        self.assertEqual(merged_person.gender, 'female')
        self.assertEqual(merged_person.honorific_prefix, 'Mr')
        self.assertEqual(merged_person.honorific_suffix, 'DBE')

        candidacies = MembershipExtra.objects.filter(
            base__person=merged_person,
            base__role=F('post_election__election__candidate_membership_role')
        ).order_by('post_election__election__election_date')

        self.assertEqual(len(candidacies), 2)
        for c, expected_election in zip(candidacies, ('2010', '2015')):
            self.assertEqual(c.post_election.election.slug, expected_election)
            self.assertEqual(c.base.post.extra.slug, '65808')

        # Check that there are only two Membership objects, since
        # there has been a bug where the MembershipExtra objects were
        # cleared on merging, but the Membership objects were left
        # behind.  So make sure there are only two as a regression
        # test.
        self.assertEqual(
            2,
            Membership.objects.filter(person=merged_person).count()
        )

        other_names = list(merged_person.other_names.all())
        self.assertEqual(len(other_names), 1)
        self.assertEqual(other_names[0].name, 'Shane Collins')

        # Check that the remaining person now has two images, i.e. the
        # one from the person to delete is added to the existing images:
        self.assertEqual(
            2,
            merged_person.extra.images.count()
        )

        primary_image = merged_person.extra.images.get(is_primary=True)
        non_primary_image = merged_person.extra.images.get(is_primary=False)

        self.assertEqual(
            primary_image.extra.user_notes, 'A photo of Tessa Jowell'
        )
        self.assertEqual(
            non_primary_image.extra.user_notes, 'A photo of Shane Collins'
        )
        self.assertEqual(mock_additional_merge_actions.call_count, 1)
        self.assertEqual(len(mock_additional_merge_actions.call_args), 2)
        self.assertEqual(mock_additional_merge_actions.call_args[0][0].id, 2009)
        # The ID will be None now because the secondary has been deleted.
        self.assertEqual(mock_additional_merge_actions.call_args[0][1].id, None)

    @patch('candidates.views.version_data.get_current_timestamp')
    @patch('candidates.views.version_data.create_version_id')
    def test_merge_regression(
            self,
            mock_create_version_id,
            mock_get_current_timestamp,
            mock_additional_merge_actions,
    ):
        mock_get_current_timestamp.return_value = example_timestamp
        mock_create_version_id.return_value = example_version_id

        # Create the primary and secondary versions of Stuart Jeffrey
        # that failed from their JSON serialization.
        stuart_primary = factories.PersonExtraFactory.create(
            base__id='2111',
            base__name='Stuart Jeffrey',
        ).base
        stuart_secondary = factories.PersonExtraFactory.create(
            base__id='12207',
            base__name='Stuart Robert Jeffrey',
        ).base

        # And create the two Westminster posts:
        factories.PostExtraFactory.create(
            elections=(self.election, self.earlier_election),
            slug='65878',
            base__label='Canterbury',
            party_set=self.gb_parties,
            base__organization=self.commons
        )
        factories.PostExtraFactory.create(
            elections=(self.election, self.earlier_election),
            slug='65936',
            base__label='Maidstone and The Weald',
            party_set=self.gb_parties,
            base__organization=self.commons
        )

        # Update each of them from the versions that were merged, and merged badly:
        revert_person_from_version_data(
            stuart_primary,
            stuart_primary.extra,
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
                    {
                        "identifier": "2111",
                        "scheme": "popit-person"
                    },
                    {
                        "identifier": "3476",
                        "scheme": "yournextmp-candidate"
                    },
                    {
                        "identifier": "15712527",
                        "scheme": "twitter"
                    }
                ],
                "image": "http://yournextmp.popit.mysociety.org/persons/2111/image/54bc790ecb19ebca71e2af8e",
                "linkedin_url": "",
                "name": "Stuart Jeffery",
                "other_names": [],
                "party_memberships": {
                    "2010": {
                        "id": "party:63",
                        "name": "Green Party"
                    },
                    "2015": {
                        "id": "party:63",
                        "name": "Green Party"
                    }
                },
                "party_ppc_page_url": "https://my.greenparty.org.uk/candidates/105873",
                "standing_in": {
                    "2010": {
                        "name": "Maidstone and The Weald",
                        "post_id": "65936"
                    },
                    "2015": {
                        "elected": False,
                        "name": "Canterbury",
                        "post_id": "65878"
                    }
                },
                "twitter_username": "stuartjeffery",
                "wikipedia_url": ""
            })

        revert_person_from_version_data(
            stuart_secondary,
            stuart_secondary.extra,
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
                        "name": "Green Party"
                    }
                },
                "party_ppc_page_url": "",
                "standing_in": {
                    "local.maidstone.2016-05-05": {
                        "elected": False,
                        "name": "Shepway South ward",
                        "post_id": "DIW:E05005004"
                    }
                },
                "twitter_username": "",
                "wikipedia_url": "",
            })

        response = self.app.get('/person/2111/update', user=self.user_who_can_merge)
        merge_form = response.forms['person-merge']
        merge_form['other'] = '12207'
        response = merge_form.submit()

        self.assertEqual(response.status_code, 302)
        self.assertEqual(
            response.location,
            '/person/2111/stuart-jeffery'
        )

        merged_person = Person.objects.get(pk='2111')

        candidacies = MembershipExtra.objects.filter(
            base__person=merged_person,
            base__role=F('post_election__election__candidate_membership_role')
        ).values_list(
            'post_election__election__slug',
            'base__post__extra__slug',
            'base__on_behalf_of__extra__slug',
        ).order_by('post_election__election__slug')

        self.assertEqual(
            list(candidacies),
            [
                (u'2010', u'65936', u'party:63'),
                (u'2015', u'65878', u'party:63'),
                (u'local.maidstone.2016-05-05', u'DIW:E05005004', u'party:63')
            ]
        )

        self.assertEqual(mock_additional_merge_actions.call_count, 1)
        self.assertEqual(len(mock_additional_merge_actions.call_args), 2)
        self.assertEqual(mock_additional_merge_actions.call_args[0][0].id, 2111)
        # The ID will be None now because the secondary has been deleted.
        self.assertEqual(mock_additional_merge_actions.call_args[0][1].id, None)
