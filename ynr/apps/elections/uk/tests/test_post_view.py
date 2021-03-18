from django.contrib.auth.models import Group
from django_webtest import WebTest

from candidates.models import TRUSTED_TO_LOCK_GROUP_NAME, LoggedAction
from candidates.tests.auth import TestUserMixin
from candidates.tests.factories import MembershipFactory
from candidates.tests.uk_examples import UK2015ExamplesMixin
from moderation_queue.models import SuggestedPostLock
from official_documents.models import OfficialDocument
from parties.tests.factories import PartyFactory
from people.tests.factories import PersonFactory


class TestBallotView(TestUserMixin, UK2015ExamplesMixin, WebTest):
    def test_suggest_post_lock_offered_with_document_when_unlocked(self):
        MembershipFactory(
            ballot=self.edinburgh_east_post_ballot,
            person=PersonFactory(),
            party=PartyFactory(),
        )
        OfficialDocument.objects.create(
            source_url="http://example.com",
            document_type=OfficialDocument.NOMINATION_PAPER,
            ballot=self.edinburgh_east_post_ballot,
            uploaded_file="sopn.pdf",
        )
        response = self.app.get(
            self.edinburgh_east_post_ballot.get_absolute_url(), user=self.user
        )
        self.assertIn("suggest_lock_form", response.forms)

    def test_suggest_post_lock_not_offered_without_document_when_unlocked(self):
        response = self.app.get(
            self.edinburgh_east_post_ballot.get_absolute_url(), user=self.user
        )
        self.assertNotIn("suggest_lock_form", response.forms)

    def test_suggest_post_lock_not_offered_with_document_when_locked(self):
        self.edinburgh_east_post_ballot.candidates_locked = True
        self.edinburgh_east_post_ballot.save()
        OfficialDocument.objects.create(
            source_url="http://example.com",
            document_type=OfficialDocument.NOMINATION_PAPER,
            ballot=self.edinburgh_east_post_ballot,
            uploaded_file="sopn.pdf",
        )
        response = self.app.get(
            self.edinburgh_east_post_ballot.get_absolute_url(), user=self.user
        )
        self.assertNotIn("suggest_lock_form", response.forms)

    def test_create_suggested_post_lock(self):
        MembershipFactory(
            ballot=self.edinburgh_east_post_ballot,
            person=PersonFactory(),
            party=PartyFactory(),
        )
        self.assertEqual(LoggedAction.objects.count(), 0)
        OfficialDocument.objects.create(
            source_url="http://example.com",
            document_type=OfficialDocument.NOMINATION_PAPER,
            ballot=self.edinburgh_east_post_ballot,
            uploaded_file="sopn.pdf",
        )
        response = self.app.get(
            self.edinburgh_east_post_ballot.get_absolute_url(), user=self.user
        )
        form = response.forms["suggest_lock_form"]
        form["justification"] = "I liked totally reviewed the SOPN"
        response = form.submit()
        self.assertEqual(response.status_code, 302)
        self.assertEqual(
            response.location,
            self.edinburgh_east_post_ballot.get_absolute_url(),
        )
        response = response.follow()
        self.assertContains(
            response,
            "Thanks, you've suggested we lock this ballot – we'll review it soon.",
        )
        suggested_locks = SuggestedPostLock.objects.all()
        self.assertEqual(suggested_locks.count(), 1)
        suggested_lock = suggested_locks.get()
        self.assertEqual(suggested_lock.ballot.post.slug, "14419")
        self.assertEqual(suggested_lock.ballot.election.slug, "parl.2015-05-07")
        self.assertEqual(suggested_lock.user, self.user)
        self.assertEqual(
            suggested_lock.justification, "I liked totally reviewed the SOPN"
        )
        self.assertEqual(LoggedAction.objects.count(), 1)
        self.assertEqual(
            LoggedAction.objects.get().source,
            "I liked totally reviewed the SOPN",
        )
        response = self.app.get("/")
        self.assertContains(response, """Suggested locking ballot""")

    def test_post_lock_disabled_not_shown_when_no_suggested_lock(self):
        group = Group.objects.get(name=TRUSTED_TO_LOCK_GROUP_NAME)
        self.user.groups.add(group)
        self.user.save()

        OfficialDocument.objects.create(
            source_url="http://example.com",
            document_type=OfficialDocument.NOMINATION_PAPER,
            ballot=self.edinburgh_east_post_ballot,
            uploaded_file="sopn.pdf",
        )

        SuggestedPostLock.objects.create(
            ballot=self.edinburgh_east_post_ballot,
            user=self.users_to_delete[-1],
            justification="I liked totally reviewed the SOPN",
        )

        SuggestedPostLock.objects.create(
            ballot=self.edinburgh_east_post_ballot_earlier,
            user=self.user,
            justification="I liked totally reviewed the SOPN",
        )

        response = self.app.get(
            self.edinburgh_east_post_ballot.get_absolute_url(), user=self.user
        )

        self.assertFalse(response.context["current_user_suggested_lock"])

        self.assertNotContains(
            response, "Locking disabled because you suggested"
        )

        self.assertNotContains(
            response, "Thanks, you've suggested we lock this list"
        )

    def test_post_lock_not_offered_when_user_suggested_lock(self):
        MembershipFactory(
            ballot=self.edinburgh_east_post_ballot,
            person=PersonFactory(),
            party=PartyFactory(),
        )
        group = Group.objects.get(name=TRUSTED_TO_LOCK_GROUP_NAME)
        self.user.groups.add(group)
        self.user.save()

        OfficialDocument.objects.create(
            source_url="http://example.com",
            document_type=OfficialDocument.NOMINATION_PAPER,
            ballot=self.edinburgh_east_post_ballot,
            uploaded_file="sopn.pdf",
        )

        SuggestedPostLock.objects.create(
            ballot=self.edinburgh_east_post_ballot,
            user=self.user,
            justification="I liked totally reviewed the SOPN",
        )

        response = self.app.get(
            self.edinburgh_east_post_ballot.get_absolute_url(), user=self.user
        )
        self.assertContains(
            response,
            "Locking disabled because you suggested locking this ballot",
        )

    def test_post_lock_offered_when_suggested_lock_exists(self):
        MembershipFactory(
            ballot=self.edinburgh_east_post_ballot,
            person=PersonFactory(),
            party=PartyFactory(),
        )
        group = Group.objects.get(name=TRUSTED_TO_LOCK_GROUP_NAME)
        self.user.groups.add(group)
        self.user.save()

        OfficialDocument.objects.create(
            source_url="http://example.com",
            document_type=OfficialDocument.NOMINATION_PAPER,
            ballot=self.edinburgh_east_post_ballot,
            uploaded_file="sopn.pdf",
        )

        SuggestedPostLock.objects.create(
            ballot=self.edinburgh_east_post_ballot,
            user=self.users_to_delete[-1],
            justification="I liked totally reviewed the SOPN",
        )

        response = self.app.get(
            self.edinburgh_east_post_ballot.get_absolute_url(), user=self.user
        )
        self.assertContains(response, "Lock candidate list")

    def test_no_lock_button_if_no_sopn(self):
        group = Group.objects.get(name=TRUSTED_TO_LOCK_GROUP_NAME)
        self.user.groups.add(group)
        self.user.save()

        SuggestedPostLock.objects.create(
            ballot=self.edinburgh_east_post_ballot,
            user=self.users_to_delete[-1],
            justification="I liked totally reviewed the SOPN",
        )

        response = self.app.get(
            self.edinburgh_east_post_ballot.get_absolute_url(), user=self.user
        )
        self.assertNotContains(response, "Lock candidate list")

    def test_no_lock_button_if_no_lock_suggestion(self):
        group = Group.objects.get(name=TRUSTED_TO_LOCK_GROUP_NAME)
        self.user.groups.add(group)
        self.user.save()

        OfficialDocument.objects.create(
            source_url="http://example.com",
            document_type=OfficialDocument.NOMINATION_PAPER,
            ballot=self.edinburgh_east_post_ballot,
            uploaded_file="sopn.pdf",
        )

        response = self.app.get(
            self.edinburgh_east_post_ballot.get_absolute_url(), user=self.user
        )
        self.assertNotContains(response, "Lock candidate list")
