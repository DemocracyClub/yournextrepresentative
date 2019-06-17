from django.utils.six import text_type
from django_webtest import WebTest

from sorl.thumbnail import get_thumbnail

from candidates.tests.auth import TestUserMixin
from candidates.tests.dates import date_in_near_future
from candidates.tests.factories import (
    MembershipFactory,
    ElectionFactory,
    MembershipFactory,
    PostFactory,
)
from people.tests.factories import PersonFactory
from candidates.tests.uk_examples import UK2015ExamplesMixin

from compat import BufferDictReader

from people.models import PersonImage, Person
from popolo.models import Membership
from moderation_queue.tests.paths import EXAMPLE_IMAGE_FILENAME
from utils.testing_utils import FuzzyInt
from uk_results.models import ResultSet


class TestConstituencyDetailView(TestUserMixin, UK2015ExamplesMixin, WebTest):
    def setUp(self):
        super().setUp()
        person = PersonFactory.create(id=2009, name="Tessa Jowell")
        dulwich_not_stand = PersonFactory.create(id=4322, name="Helen Hayes")
        MembershipFactory.create(
            person=person,
            post=self.dulwich_post,
            party=self.labour_party,
            post_election=self.dulwich_post_pee,
        )

        winner_post = self.edinburgh_east_post

        edinburgh_candidate = PersonFactory.create(
            id="818", name="Sheila Gilmore"
        )
        edinburgh_winner = PersonFactory.create(
            id="5795", name="Tommy Sheppard"
        )
        edinburgh_may_stand = PersonFactory.create(
            id="5163", name="Peter McColl"
        )

        MembershipFactory.create(
            person=dulwich_not_stand,
            post=self.dulwich_post,
            party=self.labour_party,
            post_election=self.dulwich_post_pee_earlier,
        )
        dulwich_not_stand.not_standing.add(self.election)

        MembershipFactory.create(
            person=edinburgh_winner,
            post=winner_post,
            party=self.labour_party,
            elected=True,
            post_election=self.election.postextraelection_set.get(
                post=winner_post
            ),
        )

        MembershipFactory.create(
            person=edinburgh_candidate,
            post=winner_post,
            party=self.labour_party,
            post_election=self.dulwich_post_pee,
        )

        MembershipFactory.create(
            person=edinburgh_may_stand,
            post=winner_post,
            party=self.labour_party,
            post_election=self.earlier_election.postextraelection_set.get(
                post=winner_post
            ),
        )

    def test_any_constituency_page_without_login(self):
        # Just a smoke test for the moment:
        response = self.app.get("/elections/parl.65808.2015-05-07/")
        response.mustcontain(
            '<a href="/person/2009/tessa-jowell" class="candidate-name">Tessa Jowell</a> <span class="party">Labour Party</span>'
        )
        # There should be only one form ( person search ) on the page if you're not logged in:

        # even though there is only one form on the page the list has
        # two entries - one for the numeric identifier and one for the id
        self.assertEqual(2, len(response.forms))
        self.assertEqual(response.forms[0].id, "person_search_header")

    def test_any_ballot_page(self):
        # Just a smoke test for the moment:
        with self.assertNumQueries(FuzzyInt(40, 43)):
            response = self.app.get(
                self.dulwich_post_pee.get_absolute_url(), user=self.user
            )
        response.mustcontain(
            '<a href="/person/2009/tessa-jowell" class="candidate-name">Tessa Jowell</a> <span class="party">Labour Party</span>'
        )
        form = response.forms["new-candidate-form"]
        self.assertTrue(form)
        response.mustcontain(no="Unset the current winners")

    def test_constituency_with_no_winner_record_results_user(self):
        response = self.app.get(
            self.dulwich_post_pee.get_absolute_url(),
            user=self.user_who_can_record_results,
        )
        response.mustcontain(no="Unset the current winners")

    def test_any_constituency_csv(self):
        url = "{}.csv".format(
            self.dulwich_post_pee.get_absolute_url().rstrip("/")
        )
        response = self.app.get(url)
        self.assertEqual(response.status_code, 200)
        row_dicts = [row for row in BufferDictReader(response.content)]
        self.assertEqual(2, len(row_dicts))
        self.assertDictEqual(
            dict(row_dicts[1]),
            {
                "birth_date": "",
                "cancelled_poll": "False",
                "elected": "",
                "election": "parl.2015-05-07",
                "election_current": "True",
                "election_date": text_type(date_in_near_future),
                "email": "",
                "facebook_page_url": "",
                "facebook_personal_url": "",
                "favourite_biscuits": "",
                "gender": "",
                "gss_code": "",
                "homepage_url": "",
                "honorific_prefix": "",
                "honorific_suffix": "",
                "id": "2009",
                "image_copyright": "",
                "image_uploading_user": "",
                "image_uploading_user_notes": "",
                "image_url": "",
                "linkedin_url": "",
                "mapit_url": "",
                "name": "Tessa Jowell",
                "old_person_ids": "",
                "parlparse_id": "",
                "party_ec_id": "PP53",
                "party_id": "party:53",
                "party_lists_in_use": "False",
                "party_list_position": "",
                "party_name": "Labour Party",
                "party_ppc_page_url": "",
                "post_id": "65808",
                "post_label": "Dulwich and West Norwood",
                "proxy_image_url_template": "",
                "theyworkforyou_url": "",
                "twitter_username": "",
                "twitter_user_id": "",
                "wikipedia_url": "",
                "wikidata_id": "",
            },
        )

    def test_constituency_with_winner(self):
        ResultSet.objects.create(
            post_election=self.edinburgh_east_post_pee_earlier
        )
        response = self.app.get(
            self.edinburgh_east_post_pee_earlier.get_absolute_url()
        )
        response.mustcontain("Winner(s) recorded")
        response.mustcontain(no="Winner(s) unknown")
        response.mustcontain(no="Waiting for election to happen")
        response.mustcontain(no="Unset the current winners")

    def test_constituency_with_winner_record_results_user(self):
        response = self.app.get(
            self.edinburgh_east_post_pee.get_absolute_url(),
            user=self.user_who_can_record_results,
        )
        response.mustcontain("Unset the current winners")

    def test_constituency_with_may_be_standing(self):
        response = self.app.get("/elections/parl.14419.2015-05-07/")
        response.mustcontain(
            "if these candidates from earlier elections are standing"
        )
        response.mustcontain(
            no="These candidates from earlier elections are known not to be standing again"
        )

    def test_constituency_with_not_standing(self):
        response = self.app.get(self.dulwich_post_pee.get_absolute_url())
        response.mustcontain(
            "These candidates from earlier elections are known not to be standing again"
        )
        response.mustcontain(
            no="if these candidates from earlier elections are standing"
        )

    def test_mark_not_standing_no_candidate(self):
        response = self.app.get(
            self.edinburgh_east_post_pee.get_absolute_url(), user=self.user
        )

        csrftoken = self.app.cookies["csrftoken"]
        response = self.app.post(
            "/election/2015/candidacy/delete",
            params={
                "person_id": "9999",
                "post_id": "14419",
                "source": "test data",
                "csrfmiddlewaretoken": csrftoken,
            },
            expect_errors=True,
        )

        self.assertEqual(response.status_code, 404)

    def test_mark_not_standing_no_post(self):
        response = self.app.get(
            "/election/parl.2015-05-07/post/14419/edinburgh-east",
            user=self.user,
        )

        csrftoken = self.app.cookies["csrftoken"]
        response = self.app.post(
            "/election/parl.2015-05-07/candidacy/delete",
            params={
                "person_id": "181",
                "post_id": "9999",
                "source": "test data",
                "csrfmiddlewaretoken": csrftoken,
            },
            expect_errors=True,
        )

        self.assertEqual(response.status_code, 404)

    def test_mark_standing_no_candidate(self):
        response = self.app.get(
            "/election/parl.2015-05-07/post/14419/edinburgh-east",
            user=self.user,
        )

        csrftoken = self.app.cookies["csrftoken"]
        response = self.app.post(
            "/election/parl.2015-05-07/candidacy",
            params={
                "person_id": "9999",
                "post_id": "14419",
                "source": "test data",
                "csrfmiddlewaretoken": csrftoken,
            },
            expect_errors=True,
        )

        self.assertEqual(response.status_code, 404)

    def test_mark_standing_no_post(self):
        response = self.app.get(
            "/election/parl.2015-05-07/post/14419/edinburgh-east",
            user=self.user,
        )

        csrftoken = self.app.cookies["csrftoken"]
        response = self.app.post(
            "/election/parl.2015-05-07/candidacy",
            params={
                "person_id": "5163",
                "post_id": "9999",
                "source": "test data",
                "csrfmiddlewaretoken": csrftoken,
            },
            expect_errors=True,
        )

        self.assertEqual(response.status_code, 404)

    def test_mark_candidate_not_standing(self):
        response = self.app.get(
            "/election/parl.2015-05-07/post/14419/edinburgh-east",
            user=self.user,
        )

        csrftoken = self.app.cookies["csrftoken"]
        response = self.app.post(
            "/election/parl.2015-05-07/candidacy/delete",
            params={
                "person_id": "818",
                "post_id": "14419",
                "source": "test data",
                "csrfmiddlewaretoken": csrftoken,
            },
            expect_errors=True,
        )

        membership = Membership.objects.filter(
            person_id=818,
            post__slug="14419",
            post_election__election__slug="2015",
        )
        self.assertFalse(membership.exists())

        person = Person.objects.get(id=818)
        not_standing = person.not_standing.all()
        self.assertTrue(self.election in not_standing)

        self.assertEqual(response.status_code, 302)
        self.assertEqual(
            response.location, self.edinburgh_east_post_pee.get_absolute_url()
        )

    def test_mark_may_stand_actually_standing(self):
        response = self.app.get(
            self.edinburgh_east_post_pee.get_absolute_url(), user=self.user
        )

        csrftoken = self.app.cookies["csrftoken"]
        response = self.app.post(
            "/election/parl.2015-05-07/candidacy",
            params={
                "person_id": "5163",
                "post_id": "14419",
                "source": "test data",
                "csrfmiddlewaretoken": csrftoken,
            },
            expect_errors=True,
        )

        membership = Membership.objects.filter(
            person_id=5163,
            post__slug="14419",
            post_election__election__slug="parl.2015-05-07",
        )

        self.assertTrue(membership.exists())

        self.assertEqual(response.status_code, 302)
        self.assertEqual(
            response.location, self.edinburgh_east_post_pee.get_absolute_url()
        )

    def test_mark_may_stand_not_standing_again(self):
        response = self.app.get(
            self.edinburgh_east_post_pee.get_absolute_url(), user=self.user
        )

        csrftoken = self.app.cookies["csrftoken"]
        response = self.app.post(
            "/election/parl.2015-05-07/candidacy/delete",
            params={
                "person_id": "5163",
                "post_id": "14419",
                "source": "test data",
                "csrfmiddlewaretoken": csrftoken,
            },
            expect_errors=True,
        )

        membership = Membership.objects.filter(
            person_id=5163,
            post__slug="14419",
            post_election__election__slug="parl.2015-05-07",
        )
        self.assertFalse(membership.exists())

        person = Person.objects.get(id=5163)
        not_standing = person.not_standing.all()
        self.assertTrue(self.election in not_standing)

        self.assertEqual(response.status_code, 302)
        self.assertEqual(
            response.location, self.edinburgh_east_post_pee.get_absolute_url()
        )

    def test_mark_not_standing_standing_again(self):
        response = self.app.get(
            self.dulwich_post_pee.get_absolute_url(), user=self.user
        )

        csrftoken = self.app.cookies["csrftoken"]
        response = self.app.post(
            "/election/parl.2015-05-07/candidacy",
            params={
                "person_id": "4322",
                "post_id": "65808",
                "source": "test data",
                "csrfmiddlewaretoken": csrftoken,
            },
            expect_errors=True,
        )

        membership = Membership.objects.filter(
            person_id=4322,
            post__slug="65808",
            post_election__election__slug="parl.2015-05-07",
        )

        self.assertTrue(membership.exists())

        person = Person.objects.get(id=4322)
        not_standing = person.not_standing.all()
        self.assertFalse(self.election in not_standing)

        self.assertEqual(response.status_code, 302)
        self.assertEqual(
            response.location, self.dulwich_post_pee.get_absolute_url()
        )

    def test_return_404_when_post_not_associated_with_election(self):
        # Now that post is not associated with the 2015 election, so
        # viewing a page with election: 2015 and post: DIW:E05005004
        # should return a 404.
        response = self.app.get(
            "/election/parl.2015-05-07/post/DIW:E05005004/whatever",
            expect_errors=True,
        )
        self.assertEqual(response.status_code, 404)

    def test_person_photo_shown(self):
        person = Person.objects.get(id=2009)
        im = PersonImage.objects.update_or_create_from_file(
            EXAMPLE_IMAGE_FILENAME,
            "images/imported.jpg",
            person=person,
            defaults={
                "md5sum": "md5sum",
                "copyright": "example-license",
                "uploading_user": self.user,
                "user_notes": "Here's an image...",
                "is_primary": True,
                "source": "Found on the candidate's Flickr feed",
            },
        )
        expected_url = get_thumbnail(im.image, "x64").url
        response = self.app.get(self.dulwich_post_pee.get_absolute_url())
        response.mustcontain(expected_url)
