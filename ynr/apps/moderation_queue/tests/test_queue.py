from os.path import join, realpath, dirname
import re
from shutil import rmtree

from django.contrib.auth.models import User, Group
from django.conf import settings
from django.core.files.storage import FileSystemStorage
from django.core.urlresolvers import reverse
from django.test.utils import override_settings
from django.utils.six.moves.urllib_parse import urlsplit

from PIL import Image
from io import BytesIO
from django_webtest import WebTest
from mock import patch

from people.models import Person
from moderation_queue.models import (
    QueuedImage,
    PHOTO_REVIEWERS_GROUP_NAME,
    SuggestedPostLock,
)
from candidates.models import LoggedAction, Ballot
from official_documents.models import OfficialDocument
from ynr.helpers import mkdir_p

from candidates.tests.factories import MembershipFactory
from people.tests.factories import PersonFactory
from candidates.tests.uk_examples import UK2015ExamplesMixin
from candidates.tests.auth import TestUserMixin
from moderation_queue.tests.paths import EXAMPLE_IMAGE_FILENAME

TEST_MEDIA_ROOT = realpath(join(dirname(__file__), "media"))


def get_image_type_and_dimensions(image_data):
    image = Image.open(BytesIO(image_data))
    return {
        "format": image.format,
        "width": image.size[0],
        "height": image.size[1],
    }


@override_settings(MEDIA_ROOT=TEST_MEDIA_ROOT)
class PhotoReviewTests(UK2015ExamplesMixin, WebTest):

    example_image_filename = EXAMPLE_IMAGE_FILENAME

    @classmethod
    def setUpClass(cls):
        super(PhotoReviewTests, cls).setUpClass()
        storage = FileSystemStorage()
        desired_storage_path = join("queued-images", "pilot.jpg")
        with open(cls.example_image_filename, "rb") as f:
            cls.storage_filename = storage.save(desired_storage_path, f)
        mkdir_p(TEST_MEDIA_ROOT)

    @classmethod
    def tearDownClass(cls):
        rmtree(TEST_MEDIA_ROOT)
        super(PhotoReviewTests, cls).tearDownClass()

    def setUp(self):
        super().setUp()
        person_2009 = PersonFactory.create(id=2009, name="Tessa Jowell")
        person_2007 = PersonFactory.create(id=2007, name="Tessa Jowell")
        MembershipFactory.create(
            person=person_2009,
            post=self.dulwich_post,
            party=self.labour_party,
            post_election=self.dulwich_post_pee,
        )
        MembershipFactory.create(
            person=person_2007,
            post=self.dulwich_post,
            party=self.labour_party,
            post_election=self.dulwich_post_pee,
        )

        self.test_upload_user = User.objects.create_user(
            "john", "john@example.com", "notagoodpassword"
        )
        self.test_upload_user.terms_agreement.assigned_to_dc = True
        self.test_upload_user.terms_agreement.save()
        self.test_reviewer = User.objects.create_superuser(
            "jane", "jane@example.com", "alsonotagoodpassword"
        )
        self.test_reviewer.terms_agreement.assigned_to_dc = True
        self.test_reviewer.terms_agreement.save()
        self.test_reviewer.groups.add(
            Group.objects.get(name=PHOTO_REVIEWERS_GROUP_NAME)
        )
        self.q1 = QueuedImage.objects.create(
            why_allowed="public-domain",
            justification_for_use="It's their Twitter avatar",
            decision="undecided",
            image=self.storage_filename,
            person=person_2009,
            user=self.test_upload_user,
        )
        self.q2 = QueuedImage.objects.create(
            why_allowed="copyright-assigned",
            justification_for_use="I took this last week",
            decision="approved",
            image=self.storage_filename,
            person=person_2007,
            user=self.test_upload_user,
        )
        self.q3 = QueuedImage.objects.create(
            why_allowed="other",
            justification_for_use="I found it somewhere",
            decision="rejected",
            image=self.storage_filename,
            person=person_2007,
            user=self.test_reviewer,
        )
        self.q_no_uploading_user = QueuedImage.objects.create(
            why_allowed="profile-photo",
            justification_for_use="Auto imported from Twitter",
            decision="undecided",
            image=self.storage_filename,
            person=person_2009,
            user=None,
        )

    def tearDown(self):
        self.q1.delete()
        self.q2.delete()
        self.q3.delete()
        self.test_upload_user.delete()
        self.test_reviewer.delete()
        super().tearDown()

    def test_photo_review_queue_view_not_logged_in(self):
        queue_url = reverse("photo-review-list")
        response = self.app.get(queue_url)
        self.assertEqual(response.status_code, 302)
        split_location = urlsplit(response.location)
        self.assertEqual("/accounts/login/", split_location.path)
        self.assertEqual("next=/moderation/photo/review", split_location.query)

    def test_photo_review_queue_view_logged_in_unprivileged(self):
        queue_url = reverse("photo-review-list")
        response = self.app.get(
            queue_url, user=self.test_upload_user, expect_errors=True
        )
        self.assertEqual(response.status_code, 403)

    def test_photo_review_queue_view_logged_in_privileged(self):
        queue_url = reverse("photo-review-list")
        response = self.app.get(queue_url, user=self.test_reviewer)
        self.assertEqual(response.status_code, 200)
        queue_table = response.html.find("table")
        photo_rows = queue_table.find_all("tr")
        self.assertEqual(3, len(photo_rows))
        cells = photo_rows[1].find_all("td")
        self.assertEqual(cells[2].text, "john")
        self.assertEqual(cells[3].text, "2009")
        a = cells[4].find("a")
        link_text = re.sub(r"\s+", " ", a.text).strip()
        link_url = a["href"]
        self.assertEqual(link_text, "Review")
        self.assertEqual(
            link_url, "/moderation/photo/review/{}".format(self.q1.id)
        )

    def test_photo_review_view_unprivileged(self):
        review_url = reverse(
            "photo-review", kwargs={"queued_image_id": self.q1.id}
        )
        response = self.app.get(
            review_url, user=self.test_upload_user, expect_errors=True
        )
        self.assertEqual(response.status_code, 403)

    def test_photo_review_view_privileged(self):
        review_url = reverse(
            "photo-review", kwargs={"queued_image_id": self.q1.id}
        )
        response = self.app.get(review_url, user=self.test_reviewer)
        self.assertEqual(response.status_code, 200)

    def test_shows_photo_policy_text_in_photo_review_page(self):
        review_url = reverse(
            "photo-review", kwargs={"queued_image_id": self.q1.id}
        )
        response = self.app.get(review_url, user=self.test_reviewer)
        self.assertContains(response, "Photo policy")

    @patch("moderation_queue.views.send_mail")
    @override_settings(DEFAULT_FROM_EMAIL="admins@example.com")
    def test_photo_review_upload_approved_privileged(self, mock_send_mail):
        with self.settings(SITE_ID=1):
            review_url = reverse(
                "photo-review", kwargs={"queued_image_id": self.q1.id}
            )
            review_page_response = self.app.get(
                review_url, user=self.test_reviewer
            )
            form = review_page_response.forms["photo-review-form"]
            form["decision"] = "approved"
            form["moderator_why_allowed"] = "profile-photo"
            response = form.submit(user=self.test_reviewer)
            # FIXME: check that mocked_person_put got the right calls
            self.assertEqual(response.status_code, 302)
            split_location = urlsplit(response.location)
            self.assertEqual("/moderation/photo/review", split_location.path)

            mock_send_mail.assert_called_once_with(
                "example.com image upload approved",
                "Thank you for submitting a photo to example.com. It has been\nuploaded to the candidate page here:\n\n  http://testserver/person/2009/tessa-jowell\n\nMany thanks from the example.com volunteers\n",
                "admins@example.com",
                ["john@example.com"],
                fail_silently=False,
            )

            person = Person.objects.get(id=2009)
            image = person.images.last()

            self.assertTrue(image.is_primary)
            self.assertEqual(
                "Uploaded by john: Approved from photo moderation queue",
                image.source,
            )
            self.assertEqual(427, image.image.width)
            self.assertEqual(639, image.image.height)

            self.q1.refresh_from_db()
            self.assertEqual("public-domain", self.q1.why_allowed)
            self.assertEqual("approved", self.q1.decision)
            las = LoggedAction.objects.all()
            self.assertEqual(1, len(las))
            la = las[0]
            self.assertEqual(la.user.username, "jane")
            self.assertEqual(la.action_type, "photo-approve")
            self.assertEqual(la.person.id, 2009)

            self.assertEqual(
                QueuedImage.objects.get(pk=self.q1.id).decision, "approved"
            )

    @patch("moderation_queue.views.send_mail")
    @override_settings(DEFAULT_FROM_EMAIL="admins@example.com")
    @override_settings(SUPPORT_EMAIL="support@example.com")
    def test_photo_review_upload_rejected_privileged(self, mock_send_mail):
        with self.settings(SITE_ID=1):
            review_url = reverse(
                "photo-review", kwargs={"queued_image_id": self.q1.id}
            )
            review_page_response = self.app.get(
                review_url, user=self.test_reviewer
            )
            form = review_page_response.forms["photo-review-form"]
            form["decision"] = "rejected"
            form[
                "rejection_reason"
            ] = "There's no clear source or copyright statement"
            response = form.submit(user=self.test_reviewer)
            self.assertEqual(response.status_code, 302)
            split_location = urlsplit(response.location)
            self.assertEqual("/moderation/photo/review", split_location.path)

            las = LoggedAction.objects.all()
            self.assertEqual(1, len(las))
            la = las[0]
            self.assertEqual(la.user.username, "jane")
            self.assertEqual(la.action_type, "photo-reject")
            self.assertEqual(la.person.id, 2009)
            self.assertEqual(la.source, "Rejected a photo upload from john")

            mock_send_mail.assert_called_once_with(
                "example.com image moderation results",
                "Thank-you for uploading a photo of Tessa Jowell to example.com,\nbut unfortunately we can't use that image because:\n\n  There's no clear source or copyright statement\n\nYou can just reply to this email if you want to discuss that\nfurther, or you can try uploading a photo with a different\nreason or justification for its use using this link:\n\n  http://testserver/moderation/photo/upload/2009\n\nMany thanks from the example.com volunteers\n\n--\nFor administrators' use: http://testserver/moderation/photo/review/{}\n".format(
                    self.q1.id
                ),
                "admins@example.com",
                ["john@example.com", "support@example.com"],
                fail_silently=False,
            )

            self.assertEqual(
                QueuedImage.objects.get(pk=self.q1.id).decision, "rejected"
            )

    @patch("moderation_queue.views.send_mail")
    @override_settings(DEFAULT_FROM_EMAIL="admins@example.com")
    def test_photo_review_upload_undecided_privileged(self, mock_send_mail):
        review_url = reverse(
            "photo-review", kwargs={"queued_image_id": self.q1.id}
        )
        review_page_response = self.app.get(review_url, user=self.test_reviewer)
        form = review_page_response.forms["photo-review-form"]
        form["decision"] = "undecided"
        form["rejection_reason"] = "No clear source or copyright statement"
        response = form.submit(user=self.test_reviewer)
        self.assertEqual(response.status_code, 302)
        split_location = urlsplit(response.location)
        self.assertEqual("/moderation/photo/review", split_location.path)

        self.assertEqual(mock_send_mail.call_count, 0)

        self.assertEqual(
            QueuedImage.objects.get(pk=self.q1.id).decision, "undecided"
        )

    @patch("moderation_queue.views.send_mail")
    @override_settings(DEFAULT_FROM_EMAIL="admins@example.com")
    def test_photo_review_upload_ignore_privileged(self, mock_send_mail):
        review_url = reverse(
            "photo-review", kwargs={"queued_image_id": self.q1.id}
        )
        review_page_response = self.app.get(review_url, user=self.test_reviewer)
        form = review_page_response.forms["photo-review-form"]
        form["decision"] = "ignore"
        response = form.submit(user=self.test_reviewer)
        self.assertEqual(response.status_code, 302)
        split_location = urlsplit(response.location)
        self.assertEqual("/moderation/photo/review", split_location.path)

        self.assertEqual(mock_send_mail.call_count, 0)

        self.assertEqual(
            QueuedImage.objects.get(pk=self.q1.id).decision, "ignore"
        )

        las = LoggedAction.objects.all()
        self.assertEqual(1, len(las))
        la = las[0]
        self.assertEqual(la.user.username, "jane")
        self.assertEqual(la.action_type, "photo-ignore")
        self.assertEqual(la.person.id, 2009)

    @patch("moderation_queue.views.send_mail")
    @override_settings(DEFAULT_FROM_EMAIL="admins@example.com")
    def test_photo_review_upload_approved_privileged_no_uploading_user(
        self, mock_send_mail
    ):
        with self.settings(SITE_ID=1):
            review_url = reverse(
                "photo-review",
                kwargs={"queued_image_id": self.q_no_uploading_user.id},
            )
            review_page_response = self.app.get(
                review_url, user=self.test_reviewer
            )
            form = review_page_response.forms["photo-review-form"]
            form["decision"] = "approved"
            form["moderator_why_allowed"] = "profile-photo"
            response = form.submit(user=self.test_reviewer)
            self.assertEqual(response.status_code, 302)
            split_location = urlsplit(response.location)
            self.assertEqual("/moderation/photo/review", split_location.path)

            mock_send_mail.assertFalse(mock_send_mail.called)

            person = Person.objects.get(id=2009)
            image = person.images.last()

            self.assertTrue(image.is_primary)
            self.assertEqual(
                "Uploaded by a script: Approved from photo moderation queue",
                image.source,
            )
            self.assertEqual(427, image.image.width)
            self.assertEqual(639, image.image.height)

            self.q_no_uploading_user.refresh_from_db()
            self.assertEqual(
                "profile-photo", self.q_no_uploading_user.why_allowed
            )
            self.assertEqual("approved", self.q_no_uploading_user.decision)
            las = LoggedAction.objects.all()
            self.assertEqual(1, len(las))
            la = las[0]
            self.assertEqual(la.user.username, "jane")
            self.assertEqual(la.action_type, "photo-approve")
            self.assertEqual(la.person.id, 2009)

            self.assertEqual(
                QueuedImage.objects.get(
                    pk=self.q_no_uploading_user.id
                ).decision,
                "approved",
            )

    @patch("moderation_queue.views.send_mail")
    @override_settings(DEFAULT_FROM_EMAIL="admins@example.com")
    @override_settings(SUPPORT_EMAIL="support@example.com")
    def test_photo_review_upload_rejected_privileged_no_uploading_user(
        self, mock_send_mail
    ):
        with self.settings(SITE_ID=1):
            review_url = reverse(
                "photo-review",
                kwargs={"queued_image_id": self.q_no_uploading_user.id},
            )
            review_page_response = self.app.get(
                review_url, user=self.test_reviewer
            )
            form = review_page_response.forms["photo-review-form"]
            form["decision"] = "rejected"

            response = form.submit(user=self.test_reviewer)
            self.assertEqual(response.status_code, 302)
            split_location = urlsplit(response.location)
            self.assertEqual("/moderation/photo/review", split_location.path)

            las = LoggedAction.objects.all()
            self.assertEqual(1, len(las))
            la = las[0]
            self.assertEqual(la.user.username, "jane")
            self.assertEqual(la.action_type, "photo-reject")
            self.assertEqual(la.person.id, 2009)
            self.assertEqual(la.source, "Rejected a photo upload from a script")

            self.assertFalse(mock_send_mail.called)

            self.assertEqual(
                QueuedImage.objects.get(
                    pk=self.q_no_uploading_user.id
                ).decision,
                "rejected",
            )


class SuggestedLockReviewTests(UK2015ExamplesMixin, TestUserMixin, WebTest):
    def setUp(self):
        super().setUp()
        person_2009 = PersonFactory.create(id=2009, name="Tessa Jowell")
        person_2007 = PersonFactory.create(id=2007, name="Tessa Jowell")
        MembershipFactory.create(
            person=person_2009,
            post=self.dulwich_post,
            party=self.labour_party,
            post_election=self.dulwich_post_pee,
        )
        MembershipFactory.create(
            person=person_2007,
            post=self.dulwich_post,
            party=self.labour_party,
            post_election=self.dulwich_post_pee,
        )

    def test_login_required(self):
        url = reverse("suggestions-to-lock-review-list")
        response = self.app.get(url)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(
            response.location, "/accounts/login/?next=/moderation/suggest-lock/"
        )

    def test_suggested_lock_review_view_no_suggestions(self):
        url = reverse("suggestions-to-lock-review-list")
        response = self.app.get(url, user=self.user_who_can_lock)
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, "<h3>")

    def test_suggested_lock_review_view_with_suggestions(self):
        ballot = Ballot.objects.get(
            post=self.dulwich_post, election=self.election
        )
        SuggestedPostLock.objects.create(
            ballot=ballot, user=self.user, justification="test data"
        )
        OfficialDocument.objects.create(
            document_type=OfficialDocument.NOMINATION_PAPER,
            post_election=ballot,
            source_url="http://example.com",
        )
        url = reverse("suggestions-to-lock-review-list")
        response = self.app.get(url, user=self.user_who_can_lock)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "<h3>")


class SOPNReviewRequiredTest(UK2015ExamplesMixin, TestUserMixin, WebTest):
    def test_sopn_review_view_no_reviews(self):
        url = reverse("sopn-review-required")
        response = self.app.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, "Add candidates")

    def test_sopn_review_view_with_reviews(self):
        OfficialDocument.objects.create(
            document_type=OfficialDocument.NOMINATION_PAPER,
            post_election=self.dulwich_post_pee,
            source_url="http://example.com",
        )
        url = reverse("sopn-review-required")
        response = self.app.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Dulwich")

    def test_sopn_review_view_document_with_suggested_lock_not_included(self):
        ballot = self.dulwich_post.ballot_set.get(election=self.election)
        SuggestedPostLock.objects.create(
            ballot=ballot, user=self.user, justification="test data"
        )
        OfficialDocument.objects.create(
            document_type=OfficialDocument.NOMINATION_PAPER,
            post_election=self.dulwich_post_pee,
            source_url="http://example.com",
        )
        url = reverse("sopn-review-required")
        response = self.app.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, "Dulwich")

    def test_sopn_review_view_document_with_lock_not_included(self):
        ballot = self.dulwich_post.ballot_set.get(election=self.election)
        ballot.candidates_locked = True
        ballot.save()
        OfficialDocument.objects.create(
            document_type=OfficialDocument.NOMINATION_PAPER,
            post_election=self.dulwich_post_pee,
            source_url="http://example.com",
        )
        url = reverse("sopn-review-required")
        response = self.app.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, "Dulwich")
