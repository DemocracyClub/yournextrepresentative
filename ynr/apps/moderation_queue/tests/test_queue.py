import re
from io import BytesIO
from os.path import dirname, join, realpath
from shutil import rmtree
from urllib.parse import urlsplit

from candidates.models import LoggedAction
from candidates.models.popolo_extra import Ballot
from candidates.tests.auth import TestUserMixin
from candidates.tests.factories import (
    ElectionFactory,
    MembershipFactory,
    PostFactory,
)
from candidates.tests.uk_examples import UK2015ExamplesMixin
from django.contrib.auth.models import Group, User
from django.core.files.storage import FileSystemStorage
from django.test.utils import override_settings
from django.urls import reverse
from django.utils import timezone
from django.utils.formats import date_format
from django_webtest import WebTest
from mock import patch
from moderation_queue.models import (
    PHOTO_REVIEWERS_GROUP_NAME,
    QueuedImage,
    SuggestedPostLock,
)
from moderation_queue.tests.paths import EXAMPLE_IMAGE_FILENAME
from official_documents.models import OfficialDocument
from parties.tests.factories import PartyFactory
from people.models import Person
from people.tests.factories import PersonFactory
from PIL import Image
from popolo.models import OtherName
from utils.testing_utils import FuzzyInt

from ynr.helpers import mkdir_p
from ynr.settings.constants.formats.en.formats import (
    DATE_FORMAT,
    DATETIME_FORMAT,
)

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
            ballot=self.dulwich_post_ballot,
        )
        MembershipFactory.create(
            person=person_2007,
            post=self.dulwich_post,
            party=self.labour_party,
            ballot=self.dulwich_post_ballot,
        )

        self.test_upload_user = User.objects.create_user(
            "john", "john@example.com", "notagoodpassword"
        )
        self.test_reviewer = User.objects.create_superuser(
            "jane", "jane@example.com", "alsonotagoodpassword"
        )
        group, _ = Group.objects.get_or_create(name=PHOTO_REVIEWERS_GROUP_NAME)
        self.test_reviewer.groups.add(group)
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
        with self.assertNumQueries(FuzzyInt(38, 41)):
            response = self.app.get(queue_url, user=self.test_reviewer)
        self.assertEqual(response.status_code, 200)
        queue_table = response.html.find("table")
        photo_rows = queue_table.find_all("tr")
        self.assertEqual(3, len(photo_rows))
        cells = photo_rows[1].find_all("td")

        self.assertEqual(
            cells[1].text,
            date_format(
                timezone.localtime(self.q1.created),
                format=DATETIME_FORMAT,
            ),
        )
        self.assertEqual(
            cells[2].text,
            date_format(
                self.dulwich_post_ballot.election.election_date,
                format=DATE_FORMAT,
            ),
        )
        self.assertEqual(cells[3].text, "john")
        self.assertEqual(cells[4].text, "2009")
        self.assertEqual(cells[5].text, "Review")
        a = cells[5].find("a")
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

    def test_photo_review_rotate_photo_privileged(self):
        self.assertEqual(428, self.q1.image.width)
        self.assertEqual(640, self.q1.image.height)
        review_url = reverse(
            "photo-review", kwargs={"queued_image_id": self.q1.id}
        )
        self.assertFalse(self.q1.rotation_tried)

        response = self.app.get(review_url, user=self.test_reviewer)
        form = response.forms["photo-review-form"]
        response = form.submit(name="rotate", value="right")
        self.q1.refresh_from_db()
        self.assertEqual(640, self.q1.image.width)
        self.assertEqual(428, self.q1.image.height)
        self.assertEqual(response.status_code, 302)
        self.assertTrue(self.q1.rotation_tried)
        split_location = urlsplit(response.location)
        self.assertEqual(
            "/moderation/photo/review/{}".format(self.q1.id),
            split_location.path,
        )

    @patch("moderation_queue.forms.send_mail")
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
            self.assertFalse(self.q1.rotation_tried)
            response = form.submit(user=self.test_reviewer)
            self.assertFalse(self.q1.rotation_tried)
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
            image = person.image

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

    @patch("moderation_queue.forms.send_mail")
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

    @patch("moderation_queue.forms.send_mail")
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

    @patch("moderation_queue.forms.send_mail")
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

    @patch("moderation_queue.forms.send_mail")
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

            mock_send_mail.assert_not_called()

            person = Person.objects.get(id=2009)
            image = person.image

            self.assertEqual(
                "Uploaded by a robot 🤖: Approved from photo moderation queue",
                image.source,
            )
            self.assertFalse(self.q1.rotation_tried)
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

    @patch("moderation_queue.forms.send_mail")
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
            self.assertEqual(
                la.source, "Rejected a photo upload from a robot 🤖"
            )

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
            ballot=self.dulwich_post_ballot,
        )
        MembershipFactory.create(
            person=person_2007,
            post=self.dulwich_post,
            party=self.labour_party,
            ballot=self.dulwich_post_ballot,
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
        ballot = self.dulwich_post_ballot
        SuggestedPostLock.objects.create(
            ballot=ballot, user=self.user, justification="test data"
        )
        OfficialDocument.objects.create(
            document_type=OfficialDocument.NOMINATION_PAPER,
            ballot=ballot,
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
            ballot=self.dulwich_post_ballot,
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
            ballot=self.dulwich_post_ballot,
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
            ballot=self.dulwich_post_ballot,
            source_url="http://example.com",
        )
        url = reverse("sopn-review-required")
        response = self.app.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, "Dulwich")


class PersonNameEditReviewTest(TestUserMixin, WebTest):
    def setUp(self):
        super().setUp()
        self.person = PersonFactory.create(id=2009, name="Tessa Jowell")
        self.post = PostFactory.create(label="Dulwich and West Norwood")
        self.party = PartyFactory.create(name="Labour Party")
        self.ballot = Ballot.objects.create(
            post=self.post, election=ElectionFactory.create()
        )

        MembershipFactory.create(
            person=self.person,
            post=self.post,
            party=self.party,
            ballot=self.ballot,
        )
        self.other_name = self.person.other_names.create(
            name="Tessa Palmer",
            needs_review=True,
        )

    def test_approve_name_change(self):
        # assert that the person has an other name that needs review
        self.assertTrue(OtherName.objects.filter(needs_review=True).exists())
        user = User.objects.get(username="george")
        self.client.post(
            path=reverse(
                "person-name-review",
            ),
            user=user,
            params={
                "decision": "approve",
                "pk": self.other_name.pk,
            },
        )
        self.assertTrue("Tessa Palmer", self.person.name)
        self.assertTrue(self.other_name.needs_review, False)

    def test_ignore_name_change(self):
        # assert that the person has an other name that needs review
        self.assertTrue(OtherName.objects.filter(needs_review=True).exists())
        user = User.objects.get(username="george")
        # approve the name change
        self.client.post(
            path=reverse(
                "person-name-review",
            ),
            user=user,
            params={
                "decision": "ignore",
                "pk": self.other_name.pk,
            },
        )
        # assert that the person still has the original name
        self.assertTrue("Tessa Jowell", self.person.name)
        self.assertTrue(self.other_name.needs_review, False)

    def test_reject_name_change(self):
        # assert that the person has an other name that needs review
        self.assertTrue(OtherName.objects.filter(needs_review=True).exists())
        user = User.objects.get(username="george")
        # approve the name change
        self.client.post(
            path=reverse(
                "person-name-review",
            ),
            user=user,
            params={
                "decision": "reject",
                "pk": self.other_name.pk,
            },
        )
        # assert that the name has not been changed
        self.assertTrue("Tessa Jowell", self.person.name)
        self.assertTrue(self.other_name.needs_review, False)
