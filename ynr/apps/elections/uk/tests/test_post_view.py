from django_webtest import WebTest
from django.contrib.auth.models import Group

from moderation_queue.models import SuggestedPostLock
from official_documents.models import OfficialDocument

from candidates.models import PostExtraElection, TRUSTED_TO_LOCK_GROUP_NAME
from candidates.tests.auth import TestUserMixin
from candidates.tests.uk_examples import UK2015ExamplesMixin


class TestConstituencyDetailView(TestUserMixin, UK2015ExamplesMixin, WebTest):
    def test_suggest_post_lock_offered_with_document_when_unlocked(self):
        OfficialDocument.objects.create(
            election=self.election,
            post=self.edinburgh_east_post_extra.base,
            source_url="http://example.com",
            document_type=OfficialDocument.NOMINATION_PAPER,
            post_election=self.edinburgh_east_post_extra_pee,
            uploaded_file="sopn.pdf",
        )
        response = self.app.get(
            "/election/2015/post/14419/edinburgh-east", user=self.user
        )
        self.assertIn("suggest_lock_form", response.forms)

    def test_suggest_post_lock_not_offered_without_document_when_unlocked(self):
        response = self.app.get(
            "/election/2015/post/14419/edinburgh-east", user=self.user
        )
        self.assertNotIn("suggest_lock_form", response.forms)

    def test_suggest_post_lock_not_offered_with_document_when_locked(self):
        pee = PostExtraElection.objects.get(
            election__slug="2015", postextra__slug="14419"
        )
        pee.candidates_locked = True
        pee.save()
        OfficialDocument.objects.create(
            election=self.election,
            post=self.edinburgh_east_post_extra.base,
            source_url="http://example.com",
            document_type=OfficialDocument.NOMINATION_PAPER,
            post_election=self.edinburgh_east_post_extra_pee,
            uploaded_file="sopn.pdf",
        )
        response = self.app.get(
            "/election/2015/post/14419/edinburgh-east", user=self.user
        )
        self.assertNotIn("suggest_lock_form", response.forms)

    def test_create_suggested_post_lock(self):
        OfficialDocument.objects.create(
            election=self.election,
            post=self.edinburgh_east_post_extra.base,
            source_url="http://example.com",
            document_type=OfficialDocument.NOMINATION_PAPER,
            post_election=self.edinburgh_east_post_extra_pee,
            uploaded_file="sopn.pdf",
        )
        response = self.app.get(
            "/election/2015/post/14419/edinburgh-east", user=self.user
        )
        form = response.forms["suggest_lock_form"]
        form["justification"] = "I liked totally reviewed the SOPN"
        response = form.submit()
        self.assertEqual(response.status_code, 302)
        self.assertEqual(
            response.location, "/election/2015/post/14419/edinburgh-east"
        )

        suggested_locks = SuggestedPostLock.objects.all()
        self.assertEqual(suggested_locks.count(), 1)
        suggested_lock = suggested_locks.get()
        self.assertEqual(
            suggested_lock.postextraelection.postextra.slug, "14419"
        )
        self.assertEqual(suggested_lock.postextraelection.election.slug, "2015")
        self.assertEqual(suggested_lock.user, self.user)
        self.assertEqual(
            suggested_lock.justification, "I liked totally reviewed the SOPN"
        )

    def test_post_lock_disabled_not_shown_when_no_suggested_lock(self):
        group = Group.objects.get(name=TRUSTED_TO_LOCK_GROUP_NAME)
        self.user.groups.add(group)
        self.user.save()

        OfficialDocument.objects.create(
            election=self.election,
            post=self.edinburgh_east_post_extra.base,
            source_url="http://example.com",
            document_type=OfficialDocument.NOMINATION_PAPER,
            post_election=self.edinburgh_east_post_extra_pee,
            uploaded_file="sopn.pdf",
        )

        pee = PostExtraElection.objects.get(
            election__slug="2015", postextra__slug="14419"
        )

        SuggestedPostLock.objects.create(
            postextraelection=pee,
            user=self.users_to_delete[-1],
            justification="I liked totally reviewed the SOPN",
        )

        SuggestedPostLock.objects.create(
            postextraelection=PostExtraElection.objects.get(
                election__slug="2010", postextra__slug="14419"
            ),
            user=self.user,
            justification="I liked totally reviewed the SOPN",
        )

        response = self.app.get(
            "/election/2015/post/14419/edinburgh-east", user=self.user
        )

        self.assertFalse(response.context["current_user_suggested_lock"])

        self.assertNotContains(
            response, "Locking disabled because you suggested"
        )

        self.assertNotContains(
            response, "Thanks, you've suggested we lock this list"
        )

    def test_post_lock_not_offered_when_user_suggested_lock(self):
        group = Group.objects.get(name=TRUSTED_TO_LOCK_GROUP_NAME)
        self.user.groups.add(group)
        self.user.save()

        OfficialDocument.objects.create(
            election=self.election,
            post=self.edinburgh_east_post_extra.base,
            source_url="http://example.com",
            document_type=OfficialDocument.NOMINATION_PAPER,
            post_election=self.edinburgh_east_post_extra_pee,
            uploaded_file="sopn.pdf",
        )

        pee = PostExtraElection.objects.get(
            election__slug="2015", postextra__slug="14419"
        )

        SuggestedPostLock.objects.create(
            postextraelection=pee,
            user=self.user,
            justification="I liked totally reviewed the SOPN",
        )

        response = self.app.get(
            "/election/2015/post/14419/edinburgh-east", user=self.user
        )
        self.assertContains(
            response, "Locking disabled because you suggested locking this post"
        )

    def test_post_lock_offered_when_suggested_lock_exists(self):
        group = Group.objects.get(name=TRUSTED_TO_LOCK_GROUP_NAME)
        self.user.groups.add(group)
        self.user.save()

        OfficialDocument.objects.create(
            election=self.election,
            post=self.edinburgh_east_post_extra.base,
            source_url="http://example.com",
            document_type=OfficialDocument.NOMINATION_PAPER,
            post_election=self.edinburgh_east_post_extra_pee,
            uploaded_file="sopn.pdf",
        )

        pee = PostExtraElection.objects.get(
            election__slug="2015", postextra__slug="14419"
        )

        SuggestedPostLock.objects.create(
            postextraelection=pee,
            user=self.users_to_delete[-1],
            justification="I liked totally reviewed the SOPN",
        )

        response = self.app.get(
            "/election/2015/post/14419/edinburgh-east", user=self.user
        )
        self.assertContains(response, "Lock candidate list")

    def test_no_lock_button_if_no_sopn(self):
        group = Group.objects.get(name=TRUSTED_TO_LOCK_GROUP_NAME)
        self.user.groups.add(group)
        self.user.save()

        pee = PostExtraElection.objects.get(
            election__slug="2015", postextra__slug="14419"
        )

        SuggestedPostLock.objects.create(
            postextraelection=pee,
            user=self.users_to_delete[-1],
            justification="I liked totally reviewed the SOPN",
        )

        response = self.app.get(
            "/election/2015/post/14419/edinburgh-east", user=self.user
        )
        self.assertNotContains(response, "Lock candidate list")

    def test_no_lock_button_if_no_lock_suggestion(self):
        group = Group.objects.get(name=TRUSTED_TO_LOCK_GROUP_NAME)
        self.user.groups.add(group)
        self.user.save()

        OfficialDocument.objects.create(
            election=self.election,
            post=self.edinburgh_east_post_extra.base,
            source_url="http://example.com",
            document_type=OfficialDocument.NOMINATION_PAPER,
            post_election=self.edinburgh_east_post_extra_pee,
            uploaded_file="sopn.pdf",
        )

        pee = PostExtraElection.objects.get(
            election__slug="2015", postextra__slug="14419"
        )

        response = self.app.get(
            "/election/2015/post/14419/edinburgh-east", user=self.user
        )
        self.assertNotContains(response, "Lock candidate list")
