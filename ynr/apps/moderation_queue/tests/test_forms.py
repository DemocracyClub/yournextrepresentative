from django.test import RequestFactory, TestCase

from unittest.mock import MagicMock, patch
from moderation_queue.forms import PhotoReviewForm
from moderation_queue.models import CopyrightOptions, QueuedImage
from people.tests.factories import PersonFactory


class TestPhotoReviewForm(TestCase):
    def setUp(self) -> None:
        self.factory = RequestFactory()
        request = self.factory.get("/moderation/photo/review/1")
        request.user = MagicMock(username="mockeduser")
        queued_image = QueuedImage(pk=1)
        queued_image.person = PersonFactory()
        self.form = PhotoReviewForm(queued_image=queued_image, request=request)

    def test_process(self) -> None:
        decisions = [
            QueuedImage.APPROVED,
            QueuedImage.REJECTED,
            QueuedImage.IGNORE,
            QueuedImage.UNDECIDED,
        ]
        for decision in decisions:
            with self.subTest(msg=decision):
                with patch.object(self.form, "approved"):
                    self.form.cleaned_data = {"decision": QueuedImage.APPROVED}

                    self.form.process()
                    self.form.approved.assert_called_once()

    @patch("moderation_queue.forms.PhotoReviewForm.create_logged_action")
    @patch("moderation_queue.forms.PhotoReviewForm.send_mail")
    @patch("people.models.Person.create_person_image")
    def test_approved(
        self, mock_create_image, mock_send_mail, mock_create_logged_action
    ) -> None:
        self.form.cleaned_data = {
            "decision": QueuedImage.APPROVED,
            "x_min": 0,
            "y_min": 0,
            "x_max": 200,
            "y_max": 200,
            "moderator_why_allowed": CopyrightOptions.PUBLIC_DOMAIN,
        }
        with patch.object(self.form.queued_image, "save"):
            self.form.approved()
            self.form.queued_image.save.assert_called_once()
            mock_create_image.assert_called_once()
            mock_send_mail.assert_called_once()
            mock_create_logged_action.assert_called_once()
            self.form.create_logged_action.assert_called_once()
            self.assertEqual(
                self.form.queued_image.decision, QueuedImage.APPROVED
            )
            self.assertEqual(self.form.queued_image.crop_min_x, 0)
            self.assertEqual(self.form.queued_image.crop_min_y, 0)
            self.assertEqual(self.form.queued_image.crop_max_x, 200)
            self.assertEqual(self.form.queued_image.crop_max_y, 200)

    @patch("moderation_queue.forms.PhotoReviewForm.create_logged_action")
    @patch("moderation_queue.forms.PhotoReviewForm.send_mail")
    @patch("people.models.Person.create_person_image")
    def test_rejected(
        self, mock_create_image, mock_send_mail, mock_create_logged_action
    ) -> None:
        self.form.cleaned_data = {
            "decision": QueuedImage.REJECTED,
            "rejection_reason": "Cannot determine candidate from the group",
        }
        with patch.object(self.form.queued_image, "save"):
            self.form.rejected()
            self.form.queued_image.save.assert_called_once()
            mock_create_image.assert_not_called()
            mock_send_mail.assert_called_once()
            mock_create_logged_action.assert_called_once()
            self.assertEqual(
                self.form.queued_image.decision, QueuedImage.REJECTED
            )

    @patch("moderation_queue.forms.PhotoReviewForm.create_logged_action")
    @patch("moderation_queue.forms.PhotoReviewForm.send_mail")
    @patch("people.models.Person.create_person_image")
    def test_ignored(
        self, mock_create_image, mock_send_mail, mock_create_logged_action
    ) -> None:
        self.form.cleaned_data = {"decision": QueuedImage.IGNORE}
        with patch.object(self.form.queued_image, "save"):
            self.form.ignore()
            self.form.queued_image.save.assert_called_once()
            mock_create_image.assert_not_called()
            mock_send_mail.assert_not_called()
            mock_create_logged_action.assert_called_once()
            self.assertEqual(
                self.form.queued_image.decision, QueuedImage.IGNORE
            )

    @patch("moderation_queue.forms.PhotoReviewForm.create_logged_action")
    @patch("moderation_queue.forms.PhotoReviewForm.send_mail")
    @patch("people.models.Person.create_person_image")
    def test_undecided(
        self, mock_create_image, mock_send_mail, mock_create_logged_action
    ) -> None:
        self.form.cleaned_data = {"decision": QueuedImage.UNDECIDED}
        with patch.object(self.form.queued_image, "save"):
            self.form.undecided()
            self.form.queued_image.save.assert_called_once()
            mock_create_image.assert_not_called()
            mock_send_mail.assert_not_called()
            mock_create_logged_action.assert_not_called()
            self.assertEqual(
                self.form.queued_image.decision, QueuedImage.UNDECIDED
            )

    def test_update_message(self):
        decisions = [
            (
                QueuedImage.APPROVED,
                'Approved a photo upload from a robot 🤖 who provided the message: ""',
            ),
            (QueuedImage.REJECTED, "Rejected a photo upload from a robot 🤖"),
            (
                QueuedImage.IGNORE,
                "Ignored a photo upload from a robot 🤖 (This usually means it was a duplicate)",
            ),
        ]
        for decision in decisions:
            self.form.cleaned_data = {"decision": decision[0]}
            with self.subTest(msg=decision[0]):
                self.assertEqual(self.form.update_message, decision[1])
