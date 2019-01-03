from django_webtest import WebTest
from django.contrib.auth.models import User

from .uk_examples import UK2015ExamplesMixin

from moderation_queue.models import SuggestedPostLock


class TestPostsView(UK2015ExamplesMixin, WebTest):
    def test_single_election_posts_page(self):

        response = self.app.get("/posts")

        self.assertTrue(response.html.find("h4", text="2015 General Election"))

        self.assertTrue(
            response.html.find(
                "a", text="Member of Parliament for Camberwell and Peckham"
            )
        )

    def test_elections_link_to_constituencies_page(self):

        response = self.app.get("/posts")

        heading = response.html.find("h4", text="2015 General Election")
        heading_children = list(heading.children)
        self.assertEqual(len(heading_children), 1)
        expected_link_element = heading_children[0]
        self.assertEqual(expected_link_element.name, "a")
        self.assertEqual(expected_link_element["href"], "/elections/2015/")
        self.assertEqual(expected_link_element.text, "2015 General Election")

    def test_two_elections_posts_page(self):

        self.earlier_election.current = True
        self.earlier_election.save()

        response = self.app.get("/posts")

        self.assertTrue(response.html.find("h4", text="2010 General Election"))

        self.assertTrue(response.html.find("h4", text="2015 General Election"))

    def test_suggested_post_lock_text(self):
        pee = self.election.postextraelection_set.first()
        pee.candidates_locked = False
        SuggestedPostLock.objects.create(
            postextraelection=pee,
            user=User.objects.create(username="locking_user"),
        )
        response = self.app.get("/posts")

        self.assertTrue(response.html.find("abbr", text="🔓"))


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
