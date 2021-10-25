from os.path import dirname, join, realpath
from shutil import rmtree

from django.test.utils import override_settings
from django_webtest import WebTest
from mock import patch
from duplicates.models import DuplicateSuggestion

import people.tests.factories
from candidates.models import LoggedAction, PersonRedirect
from candidates.models.versions import revert_person_from_version_data
from candidates.views.people import MERGE_FORM_ID, SUGGESTION_FORM_ID
from candidates.tests import factories
from candidates.tests.auth import TestUserMixin
from candidates.tests.uk_examples import UK2015ExamplesMixin
from moderation_queue.tests.paths import EXAMPLE_IMAGE_FILENAME
from people.models import Person, PersonImage
from popolo.models import Membership
from ynr.helpers import mkdir_p

example_timestamp = "2014-09-29T10:11:59.216159"
example_version_id = "5aa6418325c1a0bb"

TEST_MEDIA_ROOT = realpath(join(dirname(__file__), "media"))

EXAMPLE_VERSIONS = [
    {
        "username": "symroe",
        "information_source": "Just adding example data",
        "ip": "127.0.0.1",
        "version_id": "35ec2d5821176ccc",
        "timestamp": "2014-10-28T14:32:36.835429",
        "data": {
            "name": "Tessa Jowell",
            "other_names": [{"name": "Tessa Palmer", "note": "maiden name"}],
            "id": "2009",
            "honorific_suffix": "DBE",
            "twitter_username": "",
            "candidacies": {
                "parl.65808.2010-05-06": {"party": "PP53"},
                "parl.65808.2015-05-07": {"party": "PP53"},
            },
            "gender": "female",
            "homepage_url": "",
            "birth_date": None,
            "wikipedia_url": "https://en.wikipedia.org/wiki/Tessa_Jowell",
            "email": "jowell@example.com",
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
            "id": "2009",
            "twitter_username": "",
            "candidacies": {"parl.65808.2010-05-06": {"party": "PP53"}},
            "homepage_url": "http://example.org/tessajowell",
            "birth_date": "1947",
            "wikipedia_url": "",
            "email": "tessa.jowell@example.com",
        },
    },
]


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
            versions=EXAMPLE_VERSIONS,
        )
        person.tmp_person_identifiers.create(
            value="tessa.jowell@example.com", value_type="email"
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
            ballot=self.local_ballot,
        )
        factories.MembershipFactory.create(
            person=person,
            post=self.dulwich_post,
            party=self.labour_party,
            ballot=self.dulwich_post_ballot_earlier,
        )
        # Now create Shane Collins (who we'll merge into Tessa Jowell)
        person = people.tests.factories.PersonFactory.create(
            id=2007,
            name="Shane Collins",
            gender="male",
            honorific_prefix="Mr",
            versions=[
                {
                    "data": {
                        "birth_date": None,
                        "email": "shane@gn.apc.org",
                        "facebook_page_url": "",
                        "facebook_personal_url": "",
                        "gender": "male",
                        "homepage_url": "",
                        "honorific_prefix": "Mr",
                        "honorific_suffix": "",
                        "id": "2007",
                        "identifiers": [],
                        "image": None,
                        "linkedin_url": "",
                        "name": "Shane Collins",
                        "other_names": [],
                        "party_ppc_page_url": "",
                        "proxy_image": None,
                        "candidacies": {
                            "parl.65808.2010-05-06": {"party": "PP63"}
                        },
                        "not_standing": ["parl.2015"],
                        "twitter_username": "",
                        "wikipedia_url": "",
                    },
                    "information_source": "http://www.lambeth.gov.uk/sites/default/files/ec-dulwich-and-west-norwood-candidates-and-notice-of-poll-2015.pdf",
                    "timestamp": "2015-04-09T20:32:09.237610",
                    "username": "JPCarrington",
                    "version_id": "274e50504df330e4",
                },
                {
                    "data": {
                        "birth_date": None,
                        "email": "shane@gn.apc.org",
                        "facebook_page_url": None,
                        "facebook_personal_url": None,
                        "gender": "male",
                        "homepage_url": None,
                        "id": "2007",
                        "identifiers": [],
                        "name": "Shane Collins",
                        "party_ppc_page_url": None,
                        "phone": "07939 196612",
                        "slug": "shane-collins",
                        "candidacies": {
                            "parl.65808.2010-05-06": {"party": "PP63"}
                        },
                        "twitter_username": None,
                        "wikipedia_url": None,
                    },
                    "information_source": "Imported from YourNextMP data from 2010",
                    "timestamp": "2014-11-21T18:16:47.670167",
                    "username": "JPCarrington",
                    "version_id": "68a452284d95d9ab",
                },
            ],
        )
        person.tmp_person_identifiers.create(
            value="shane@gn.apc.org", value_type="email"
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
            ballot=self.dulwich_post_ballot_earlier,
        )
        factories.MembershipFactory.create(
            person=person,
            post=self.dulwich_post,
            party=self.green_party,
            ballot=self.edinburgh_east_post_ballot,
        )

    def tearDown(self):
        # Delete the images we created in the test media root:
        rmtree(TEST_MEDIA_ROOT)

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
        response = self.app.get("/person/2009/", user=self.user_who_can_merge)

        # first submit suggestion form
        suggestion_form = response.forms[SUGGESTION_FORM_ID]
        suggestion_form["other_person"] = "2007"
        response = suggestion_form.submit()

        # then submit merge directly
        merge_form = response.forms[MERGE_FORM_ID]
        response = merge_form.submit()

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.location, "/person/2007/tessa-jowell")

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
        self.assertEqual(merged_person.get_email, "shane@gn.apc.org")
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
        found_ballots = {mem.ballot.ballot_paper_id for mem in candidacies}
        self.assertEqual(expected_ballots, found_ballots)

        # Check that there are only two Membership objects
        self.assertEqual(
            3, Membership.objects.filter(person=merged_person).count()
        )
        merged_person.refresh_from_db()
        other_names = list(merged_person.other_names.all())
        self.assertEqual(len(other_names), 1)
        self.assertEqual(other_names[0].name, "Shane Collins")
        self.assertEqual(merged_person.name, "Tessa Jowell")

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
                "birth_date": "1967",
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
                "party_ppc_page_url": "https://my.greenparty.org.uk/candidates/105873",
                "candidacies": {
                    "parl.65936.2010-05-06": {"party": "PP63"},
                    "parl.65878.2015-05-07": {
                        "elected": False,
                        "party": "PP63",
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
                "party_ppc_page_url": "",
                "candidacies": {
                    "local.maidstone.DIW:E05005004.2016-05-05": {
                        "elected": False,
                        "party": "PP63",
                    }
                },
                "twitter_username": "",
                "wikipedia_url": "",
            },
        )

        response = self.app.get("/person/2111/", user=self.user_who_can_merge)

        # first submit suggestion form
        suggestion_form = response.forms[SUGGESTION_FORM_ID]
        suggestion_form["other_person"] = "12207"
        response = suggestion_form.submit()

        # then directly merge
        merge_form = response.forms[MERGE_FORM_ID]
        response = merge_form.submit()

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.location, "/person/2111/stuart-jeffery")

        merged_person = Person.objects.get(pk="2111")

        candidacies = (
            Membership.objects.filter(person=merged_person)
            .values_list(
                "ballot__election__slug", "post__slug", "party__legacy_slug"
            )
            .order_by("ballot__election__slug")
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
            form = response.forms["person-details"]
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
        _do_edit_for_user(non_primary_person, "birth_date", "1968", "Wikipedia")

        self.assertEqual(LoggedAction.objects.count(), 4)
        self.assertEqual(Person.objects.count(), 2)
        response = self.app.get("/recent-changes")
        self.assertEqual(len(response.context["actions"].object_list), 4)

        response = self.app.get(
            "/person/{}/".format(primary_person.pk),
            user=self.user_who_can_merge,
        )

        # first submit the suggestion form
        suggestion_form = response.forms[SUGGESTION_FORM_ID]
        suggestion_form["other_person"] = non_primary_person.pk
        response = suggestion_form.submit()

        # as user has permission to merge directly, submit merge form
        merge_form = response.forms[MERGE_FORM_ID]
        response = merge_form.submit()

        self.assertEqual(Person.objects.count(), 1)
        # 5 actions, because we create a "merge" logged action
        self.assertEqual(LoggedAction.objects.count(), 5)
        response = self.app.get("/recent-changes")
        self.assertEqual(len(response.context["actions"].object_list), 5)

    def test_merge_not_standing_conflict(self):
        """
        The following is an invalid sort of merge:

        Person A: Standing in local.foo.2019-0-01
        Person B: local.foo.2019-0-01 in their "not_standing" list

        This is because a human has asserted that Person B is known not to
        be standing in the election that person A is standing in.

        It's best not to make any assumptions here, as this might indicate
        an invalid merge.

        However, in reality we commonly see this when a two people have been
        created in the same election. Because most users can't merge, the only
        option they have to de-duplicate is to mark one of the people as
        not standing.

        Someone else can then come along and merge the two people, and see the
        above condition.

        We now offer them a route out, by removing the not standing assertion,
        or abandoning everything and…doing something else?

        """
        person_a = Person.objects.create(
            pk=1,
            name="Tess Foo Jowell",
            versions=[
                {
                    "data": {
                        "birth_date": None,
                        "email": "shane@gn.apc.org",
                        "facebook_page_url": "",
                        "facebook_personal_url": "",
                        "gender": "male",
                        "homepage_url": "",
                        "honorific_prefix": "Mr",
                        "honorific_suffix": "",
                        "id": "1",
                        "identifiers": [],
                        "image": None,
                        "linkedin_url": "",
                        "name": "Shane Collins",
                        "other_names": [],
                        "candidacies": {},
                        "party_ppc_page_url": "",
                        "proxy_image": None,
                        "not_standing": ["parl.2015"],
                        "twitter_username": "",
                        "wikipedia_url": "",
                    },
                    "information_source": "http://www.lambeth.gov.uk/sites/default/files/ec-dulwich-and-west-norwood-candidates-and-notice-of-poll-2015.pdf",
                    "timestamp": "2015-04-09T20:32:09.237610",
                    "username": "JPCarrington",
                    "version_id": "274e50504df330e4",
                }
            ],
        )
        person_a.not_standing.add(self.dulwich_post_ballot.election)

        person_b = Person.objects.get(pk=2009)
        factories.MembershipFactory.create(
            person=person_b,
            post=self.dulwich_post,
            party=self.labour_party,
            ballot=self.dulwich_post_ballot,
        )

        response = self.app.get(
            "/person/{}/".format(person_a.pk), user=self.user_who_can_merge
        )

        # first submit suggestion form
        suggestion_form = response.forms[SUGGESTION_FORM_ID]
        suggestion_form["other_person"] = person_b.pk
        response = suggestion_form.submit()

        # then directly merge
        merge_form = response.forms[MERGE_FORM_ID]
        response = merge_form.submit()

        self.assertEqual(response.status_code, 302)
        self.assertEqual(
            response.location, "/person/1/merge_conflict/2009/not_standing/"
        )
        response = response.follow()
        form = response.forms[1]
        response = form.submit()
        response.follow()
        self.assertEqual(response.location, "/person/1/tessa-jowell")

    def test_merge_same_person_shows_error(self):
        response = self.app.get(
            "/person/{}/".format(2009), user=self.user_who_can_merge
        )

        suggestion_form = response.forms[SUGGESTION_FORM_ID]
        suggestion_form["other_person"] = 2009
        response = suggestion_form.submit()

        self.assertEqual(response.status_code, 200)
        self.assertContains(
            response,
            "You can&#x27;t suggest a duplicate person (2009) with themself (2009)",
        )

    def test_merge_malformed_other(self):
        response = self.app.get(
            "/person/{}/".format(2009), user=self.user_who_can_merge
        )

        suggestion_form = response.forms[SUGGESTION_FORM_ID]
        suggestion_form["other_person"] = "foobar"
        response = suggestion_form.submit()

        self.assertEqual(response.status_code, 200)
        self.assertContains(
            response, "The other person ID provided was invalid"
        )


class TestMergeViewFullyFrontEnd(TestUserMixin, UK2015ExamplesMixin, WebTest):
    def setUp(self):
        # Person 1
        response = self.app.get(
            self.dulwich_post_ballot.get_absolute_url(), user=self.user
        )
        form = response.forms["new-candidate-form"]
        form["name"] = "Elizabeth Bennet"
        form["tmp_person_identifiers-0-value"] = "lizzie@example.com"
        form["tmp_person_identifiers-0-value_type"] = "email"
        form[
            "tmp_person_identifiers-1-value"
        ] = "http://en.wikipedia.org/wiki/Lizzie_Bennet"
        form["tmp_person_identifiers-1-value_type"] = "wikipedia_url"

        form["party_identifier_1"] = self.labour_party.ec_id
        form["ballot_paper_id"] = self.camberwell_post_ballot.ballot_paper_id
        form["source"] = "bar bar"

        form.submit()

        # Person 2
        response = self.app.get(
            self.local_ballot.get_absolute_url(), user=self.user
        )
        form = response.forms["new-candidate-form"]
        form["name"] = "Foo Bar"
        election_slug = self.local_ballot.election.slug
        form["party_identifier_1"] = self.labour_party.ec_id
        form["ballot_paper_id"] = self.local_ballot.ballot_paper_id
        form["source"] = "foo bar"

        response = form.submit()

    def test_persons_created(self):
        self.assertEqual(Person.objects.all().count(), 2)

    def test_merging_people(self):

        source, dest = Person.objects.all().values_list("pk", flat=True)

        response = self.app.get(
            "/person/{}/update".format(source), user=self.user
        )

        form = response.forms[1]
        form["birth_date"] = "1962"
        form["death_date"] = "2000"
        form["source"] = "BBC News"
        form.submit().follow()

        response = self.app.get(
            "/person/{}/".format(dest), user=self.user_who_can_merge
        )
        # first submit suggestion form
        suggestion_form = response.forms[SUGGESTION_FORM_ID]
        suggestion_form["other_person"] = source
        response = suggestion_form.submit()

        # then submit merge
        merge_form = response.forms[MERGE_FORM_ID]
        merge_form.submit()

        self.assertEqual(Person.objects.count(), 1)

    def test_suggest_duplicate_people(self):
        """
        Similar to above, but user does not have merge permissions so
        cannot submit the merge but instead creates a
        DuplicateSuggestion object
        """

        source, dest = Person.objects.all().values_list("pk", flat=True)

        response = self.app.get(
            "/person/{}/update".format(source), user=self.user
        )

        form = response.forms[1]
        form["birth_date"] = "1962"
        form["death_date"] = "2000"
        form["source"] = "BBC News"
        form.submit().follow()

        response = self.app.get("/person/{}/".format(dest), user=self.user)
        # first submit suggestion form
        suggestion_form = response.forms[SUGGESTION_FORM_ID]
        suggestion_form["other_person"] = source
        response = suggestion_form.submit()

        #  merge form not in the response as user doesnt have merge permission
        assert MERGE_FORM_ID not in response.forms
        # instead confirm the suggestion
        suggestion_form = response.forms[SUGGESTION_FORM_ID]
        suggestion_form.submit()

        # still 2 people
        self.assertEqual(Person.objects.count(), 2)
        # but 1 merge suggestion
        self.assertEqual(DuplicateSuggestion.objects.count(), 1)

    def test_merge_three_people(self):
        # Merge the first two people
        source, dest = Person.objects.all().values_list("pk", flat=True)
        response = self.app.get(
            "/person/{}/".format(dest), user=self.user_who_can_merge
        )

        # first submit suggestion form
        suggestion_form = response.forms[SUGGESTION_FORM_ID]
        suggestion_form["other_person"] = source
        response = suggestion_form.submit()

        # then submit merge directly
        merge_form = response.forms[MERGE_FORM_ID]
        response = merge_form.submit()

        # Make another person
        self.earlier_election.current = True
        self.earlier_election.save()
        self.earlier_election.refresh_from_db()
        response = self.app.get(
            self.dulwich_post_ballot_earlier.get_absolute_url(), user=self.user
        )
        form = response.forms["new-candidate-form"]
        form["name"] = "Foo Bar"
        election_slug = self.earlier_election.slug
        form["party_identifier_1"] = self.labour_party.ec_id
        form[
            "ballot_paper_id"
        ] = self.dulwich_post_ballot_earlier.ballot_paper_id
        form["source"] = "foo bar"

        response = form.submit()

        # Merge again
        source, dest = Person.objects.all().values_list("pk", flat=True)
        response = self.app.get(
            "/person/{}/".format(dest), user=self.user_who_can_merge
        )

        # again submit suggestion form
        suggestion_form = response.forms[SUGGESTION_FORM_ID]
        suggestion_form["other_person"] = source
        response = suggestion_form.submit()

        # then submit merge directly
        merge_form = response.forms[MERGE_FORM_ID]
        response = merge_form.submit()

        self.assertTrue(Person.objects.count(), 1)
