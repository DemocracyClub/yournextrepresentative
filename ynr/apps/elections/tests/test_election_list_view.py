from candidates.models.popolo_extra import Ballot
from candidates.tests.test_models import BallotsWithResultsMixin
from candidates.tests.uk_examples import UK2015ExamplesMixin
from django.contrib.auth.models import User
from django.http import QueryDict
from django.test import RequestFactory, TestCase
from django_webtest import WebTest
from elections.views import ElectionListView
from mock import patch
from moderation_queue.models import SuggestedPostLock


class TestPostsView(UK2015ExamplesMixin, WebTest):
    def setUp(self):
        return super().setUp()

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
        self.assertEqual(response.context["filter"].qs.count(), 6)
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
        self.assertEqual(response.context["filter"].qs.count(), 6)
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


class TestResultsAnnotated(BallotsWithResultsMixin, TestCase):
    def setUp(self):
        self.rf = RequestFactory()
        self.request = self.rf.get("/elections/")
        self.request.GET = QueryDict(
            "has_results=1&review_required=locked&is_cancelled=0"
        )
        return super().setUp()

    def test_elections_annotated_correctly(self):
        # create 10 ballots matching out filter above
        self.create_ballots_with_results(
            num=10,
            resultset=True,
            candidates_locked=True,
            winner_count=1,
            num_winners=1,
        )

        # create 10 more with two winners each
        self.create_ballots_with_results(
            num=10,
            resultset=True,
            candidates_locked=True,
            winner_count=2,
            num_winners=2,
        )
        view = ElectionListView()
        view.setup(request=self.request)

        with patch.object(
            Ballot.objects,
            "current_or_future",
            return_value=Ballot.objects.all(),
        ):
            context = view.get_context_data()

            qs = context["queryset"]
            # expect 20 in total
            self.assertEqual(qs.count(), 20)
            # 10 where 1 person elected
            self.assertEqual(qs.filter(elected_count=1).count(), 10)
            # 10 where two people were elected
            self.assertEqual(qs.filter(elected_count=2).count(), 10)
            # all have same num candidates
            self.assertEqual(qs.filter(memberships_count=9).count(), 20)
