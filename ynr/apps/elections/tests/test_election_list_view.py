from django.contrib.auth.models import User
from django_webtest import WebTest

from candidates.tests.uk_examples import UK2015ExamplesMixin
from moderation_queue.models import SuggestedPostLock


class TestPostsView(UK2015ExamplesMixin, WebTest):
    def test_single_election_posts_page(self):

        response = self.app.get("/elections/")

        self.assertContains(response, "2015 General Election")

        self.assertTrue(
            response.html.find(
                "a", text="Member of Parliament for Camberwell and Peckham"
            )
        )

    def test_elections_link_to_constituencies_page(self):

        response = self.app.get("/elections/")
        self.assertEqual(response.context["filter"].qs.count(), 5)
        self.assertContains(response, "2015 General Election")
        self.assertContains(response, "/elections/parl.2015-05-07/")
        self.assertFalse(response.context["filter"].data)

    def test_two_elections_posts_page(self):

        self.earlier_election.current = True
        self.earlier_election.save()

        response = self.app.get("/elections/")

        self.assertContains(response, "2010 General Election")
        self.assertContains(response, "2015 General Election")

    def test_suggested_post_lock_text(self):
        ballot = self.election.ballot_set.first()
        ballot.candidates_locked = False
        SuggestedPostLock.objects.create(
            ballot=ballot, user=User.objects.create(username="locking_user")
        )
        response = self.app.get("/elections/?review_required=suggestion")

        self.assertContains(response, "🔓")

    def test_elections_filters(self):
        # Unfiltered
        response = self.app.get("/elections/")
        self.assertEqual(response.context["filter"].qs.count(), 5)
        self.assertEqual(response.context["filter"].data, {})

        # Lock suggestions, basically the same as the above test
        ballot = self.election.ballot_set.first()
        ballot.candidates_locked = False
        SuggestedPostLock.objects.create(
            ballot=ballot, user=User.objects.create(username="locking_user")
        )
        response = self.app.get("/elections/?review_required=suggestion")
        self.assertEqual(response.context["filter"].qs.count(), 1)
        self.assertEqual(
            dict(response.context["filter"].data),
            {"review_required": ["suggestion"]},
        )

        # Election type
        response = self.app.get("/elections/?election_type=local")
        self.assertEqual(response.context["filter"].qs.count(), 1)
        self.assertEqual(
            dict(response.context["filter"].data), {"election_type": ["local"]}
        )


class TestPostIDToPartySetView(UK2015ExamplesMixin, WebTest):
    def test_post_id_to_party_set_json(self):

        response = self.app.get("/post-id-to-party-set.json")
        self.assertEqual(
            response.json,
            {
                "14419": "GB",
                "14420": "GB",
                "65808": "GB",
                "65913": "GB",
                "DIW:E05005004": "GB",
            },
        )
