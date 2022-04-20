from django.test import TestCase
from django.test.client import RequestFactory
from django.urls import reverse
from candidates.tests.auth import TestUserMixin
from candidates.tests.uk_examples import UK2015ExamplesMixin
from moderation_queue.models import SuggestedPostLock

from moderation_queue.views import SuggestLockReviewListView
from django.contrib.auth import get_user_model
from django.utils.text import slugify

from candidates.tests.factories import (
    BallotPaperFactory,
    ElectionFactory,
    OrganizationFactory,
    PostFactory,
)


User = get_user_model()


def create_election(slug, **kwargs):
    return ElectionFactory.create(slug=slug, **kwargs)


def create_ballot(ballot_paper_id, ward, election):
    org = OrganizationFactory(name=f"{ward} Council", slug=slugify(ward))
    post = PostFactory(label=ward, organization=org)

    return BallotPaperFactory(
        election=election, post=post, ballot_paper_id=ballot_paper_id
    )


def create_lock_suggestion(ballot, user):
    return SuggestedPostLock.objects.create(ballot=ballot, user=user)


class TestSuggestLockReviewListView(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.request = self.factory.get("/")
        self.logged_in_user = User.objects.create(username="logged_in_user")
        self.request.user = self.logged_in_user
        self.other_user = User.objects.create(username="other_user")

        self.sheffield = create_election(
            slug="local.sheffield.2021-05-06", name="Sheffield Local Election"
        )
        self.ecclesall = create_ballot(
            ballot_paper_id="local.sheffield.ecclesall.2021-05-06",
            ward="Ecclesall",
            election=self.sheffield,
        )
        self.fulwood = create_ballot(
            ballot_paper_id="local.sheffield.fulwood.2021-05-06",
            ward="Fulwood",
            election=self.sheffield,
        )
        self.view = SuggestLockReviewListView()
        self.view.setup(request=self.request)

    def test_get_random_election_only_users_suggestion(self):
        """
        Test that when only the logged in user has created lock suggestions for
        ballots related for an election, the election is not returned
        """
        create_lock_suggestion(ballot=self.ecclesall, user=self.logged_in_user)
        create_lock_suggestion(ballot=self.fulwood, user=self.logged_in_user)

        result = self.view.get_random_election()
        self.assertIsNone(result)

    def test_get_random_election_one_other_users_lock_suggestion(self):
        """
        Test that when logged in user and another user has created a lock
        suggestion for that elections ballots, the election is returned
        """
        create_lock_suggestion(ballot=self.ecclesall, user=self.logged_in_user)
        create_lock_suggestion(ballot=self.fulwood, user=self.other_user)

        result = self.view.get_random_election()
        self.assertEqual(result, self.sheffield)

    def test_get_random_election_only_other_users_lock_suggestions(self):
        """
        Test that when only another user has created a lock suggestions for that
        elections ballots, the election is returned
        """
        create_lock_suggestion(ballot=self.ecclesall, user=self.other_user)
        create_lock_suggestion(ballot=self.fulwood, user=self.other_user)

        result = self.view.get_random_election()
        self.assertEqual(result, self.sheffield)

    def test_get_lock_suggestions_returns_all_other_users_suggestions(self):
        """
        Test that when only another user has created a lock suggestions for that
        elections ballots, all ballots are returned
        """
        create_lock_suggestion(ballot=self.ecclesall, user=self.other_user)
        create_lock_suggestion(ballot=self.fulwood, user=self.other_user)

        result = self.view.get_lock_suggestions()
        self.assertEqual(result.count(), 2)
        self.assertIn(self.ecclesall, result)
        self.assertIn(self.fulwood, result)

    def test_get_lock_suggestions_returns_one_other_users_suggestion(self):
        """
        Test that when both logged in user and another user has created a lock
        suggestions for that ballots, only ballots with lock suggestion by
        other user are returned
        """
        create_lock_suggestion(ballot=self.ecclesall, user=self.logged_in_user)
        create_lock_suggestion(ballot=self.fulwood, user=self.other_user)

        result = self.view.get_lock_suggestions()
        self.assertEqual(result.count(), 1)
        self.assertNotIn(self.ecclesall, result)
        self.assertIn(self.fulwood, result)

    def test_get_lock_suggestions_returns_empty_qs(self):
        """
        Test that when all lock suggestions are related to logged in user that
        an empty Ballot QuerySet is returned
        """
        create_lock_suggestion(ballot=self.ecclesall, user=self.logged_in_user)
        create_lock_suggestion(ballot=self.fulwood, user=self.logged_in_user)

        result = self.view.get_lock_suggestions()
        self.assertEqual(result.count(), 0)
        self.assertFalse(result.exists())

    def test_get_lock_suggestions_excludes_locked_ballots(self):
        """
        It should not be possible now for a user to create a lock
        suggestion fora locked ballot via the website. But this is a
        safeguard check to make sure that the lock suggestion would
        not appear in the review list anyway
        """
        create_lock_suggestion(ballot=self.ecclesall, user=self.other_user)
        self.ecclesall.candidates_locked = True
        self.ecclesall.save()
        queryset = self.view.get_lock_suggestions()
        self.assertEqual(queryset.count(), 0)


class TestSuggestLockView(TestUserMixin, UK2015ExamplesMixin, TestCase):
    def test_lock_suggestion_created(self):
        url = reverse(
            "constituency-suggest-lock",
            kwargs={"election_id": self.local_ballot.ballot_paper_id},
        )
        self.client.force_login(user=self.user)
        self.assertFalse(self.local_ballot.candidates_locked)
        self.assertEqual(self.local_ballot.suggestedpostlock_set.count(), 0)
        response = self.client.post(
            url,
            data={"ballot": self.local_ballot.pk, "justification": "Testing"},
            follow=True,
        )
        self.assertEqual(self.local_ballot.suggestedpostlock_set.count(), 1)
        messages = list(response.context["messages"])
        self.assertEqual(
            messages[0].message, "Thanks for suggesting we lock an area!"
        )

    def test_lock_suggestion_not_created_when_ballot_locked(self):
        self.local_ballot.candidates_locked = True
        self.local_ballot.save()
        url = reverse(
            "constituency-suggest-lock",
            kwargs={"election_id": self.local_ballot.ballot_paper_id},
        )
        self.client.force_login(user=self.user)
        self.assertEqual(self.local_ballot.suggestedpostlock_set.count(), 0)
        response = self.client.post(
            url,
            data={"ballot": self.local_ballot.pk, "justification": "Testing"},
            follow=True,
        )
        self.assertEqual(self.local_ballot.suggestedpostlock_set.count(), 0)
        messages = list(response.context["messages"])
        self.assertEqual(
            messages[0].message,
            "Cannot add a lock suggestion because candidates are already locked",
        )
