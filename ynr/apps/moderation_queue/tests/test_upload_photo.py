import os
from os.path import dirname, join, realpath
from shutil import rmtree
from urllib.parse import urlsplit

from candidates.models import LoggedAction
from candidates.tests.uk_examples import UK2015ExamplesMixin
from django.contrib.auth.models import User
from django.core.files.storage import FileSystemStorage
from django.test.utils import override_settings
from django.urls import reverse
from django_webtest import WebTest
from mock import Mock, patch
from moderation_queue.helpers import (
    ImageDownloadException,
    convert_image_to_png,
    download_image_from_url,
)
from moderation_queue.models import QueuedImage
from moderation_queue.tests.paths import (
    EXAMPLE_IMAGE_FILENAME,
    ROTATED_IMAGE_FILENAME,
    XL_IMAGE_FILENAME,
)
from people.tests.factories import PersonFactory
from PIL import Image as PillowImage
from webtest import Upload

from ynr.helpers import mkdir_p

TEST_MEDIA_ROOT = realpath(join(dirname(__file__), "media"))


@override_settings(MEDIA_ROOT=TEST_MEDIA_ROOT)
class PhotoUploadImageTests(UK2015ExamplesMixin, WebTest):

    example_image_filename = EXAMPLE_IMAGE_FILENAME
    rotated_image_filename = ROTATED_IMAGE_FILENAME
    xl_image_filename = XL_IMAGE_FILENAME

    @classmethod
    def setUpClass(cls):
        super(PhotoUploadImageTests, cls).setUpClass()
        storage = FileSystemStorage()
        desired_storage_path = join("queued-images", "pilot.jpg")
        with open(cls.example_image_filename, "rb") as f:
            cls.storage_filename = storage.save(desired_storage_path, f)
        mkdir_p(TEST_MEDIA_ROOT)

    @classmethod
    def tearDownClass(cls):
        rmtree(TEST_MEDIA_ROOT)
        super(PhotoUploadImageTests, cls).tearDownClass()

    def setUp(self):
        super().setUp()
        PersonFactory.create(id=2009, name="Tessa Jowell")
        self.test_upload_user = User.objects.create_user(
            "john", "john@example.com", "notagoodpassword"
        )

    def tearDown(self):
        super().tearDown()
        self.test_upload_user.delete()

    def invalid_form(self):
        return self.form_page_response.forms["person-upload-photo-url"]

    def valid_form(self):
        form = self.form_page_response.forms["person-upload-photo-image"]
        form["image"] = Upload(self.rotated_image_filename)
        form["justification_for_use"] = "copyright-assigned"
        form["why_allowed"] = "profile-photo"
        return form

    def get_and_head_methods(self, *all_mock_requests):
        return [
            getattr(mock_requests, attr)
            for mock_requests in all_mock_requests
            for attr in ("get", "head")
        ]

    def successful_get_rotated_image(self, *all_mock_requests, **kwargs):
        content_type = kwargs.get("content_type", "image/jpeg")
        headers = {"content-type": content_type}
        with open(self.rotated_image_filename, "rb") as image:
            image_data = image.read()
            for mock_method in self.get_and_head_methods(*all_mock_requests):
                setattr(
                    mock_method,
                    "return_value",
                    Mock(
                        status_code=200,
                        headers=headers,
                        # The chunk size is larger than the example
                        # image, so we don't need to worry about
                        # returning subsequent chunks.
                        iter_content=lambda **kwargs: [image_data],
                    ),
                )

    def successful_get_oversized_image(self, *all_mock_requests, **kwargs):
        content_type = kwargs.get("content_type", "image/jpeg")
        headers = {"content-type": content_type}
        with open(self.xl_image_filename, "rb") as image:
            image_data = image.read()
            for mock_method in self.get_and_head_methods(*all_mock_requests):
                setattr(
                    mock_method,
                    "return_value",
                    Mock(
                        status_code=200,
                        headers=headers,
                        # The chunk size is larger than the example
                        # image, so we don't need to worry about
                        # returning subsequent chunks.
                        iter_content=lambda **kwargs: [image_data],
                    ),
                )

    def test_queued_images_form_visibility(self):
        QueuedImage.objects.create(
            person_id=2009,
            user=self.test_upload_user,
            why_allowed="copyright-assigned",
            justification_for_use="I took this photo",
        )
        upload_form_url = reverse("photo-upload", kwargs={"person_id": "2009"})
        response = self.app.get(upload_form_url, user=self.test_upload_user)
        self.assertNotContains(response, "Photo policy")
        self.assertContains(
            response, "already has images in the queue waiting for review."
        )

    def test_no_queued_images_form_visibility(self):
        upload_form_url = reverse("photo-upload", kwargs={"person_id": "2009"})
        response = self.app.get(upload_form_url, user=self.test_upload_user)
        self.assertContains(response, "Photo policy")
        self.assertNotContains(
            response,
            "already has images in the queue waiting for review.You can review them here",
        )

    def test_photo_upload_through_image_field(self):
        queued_images = QueuedImage.objects.all()
        initial_count = queued_images.count()
        upload_form_url = reverse("photo-upload", kwargs={"person_id": "2009"})
        form_page_response = self.app.get(
            upload_form_url, user=self.test_upload_user
        )
        form = form_page_response.forms["person-upload-photo-image"]
        with open(self.example_image_filename, "rb") as f:
            form["image"] = Upload("pilot.jpg", f.read())
        form["why_allowed"] = "copyright-assigned"
        form["justification_for_use"] = "I took this photo"
        upload_response = form.submit()
        self.assertEqual(upload_response.status_code, 302)

        split_location = urlsplit(upload_response.location)
        self.assertEqual(
            "/moderation/photo/upload/2009/success", split_location.path
        )

        queued_images = QueuedImage.objects.all()
        self.assertEqual(initial_count + 1, queued_images.count())

        queued_image = queued_images.last()
        self.assertEqual(queued_image.decision, "undecided")
        self.assertEqual(queued_image.why_allowed, "copyright-assigned")
        self.assertEqual(
            queued_image.justification_for_use, "I took this photo"
        )
        self.assertEqual(queued_image.person.id, 2009)
        self.assertEqual(queued_image.user, self.test_upload_user)

        # check the image was converted to a png on upload
        self.assertTrue(queued_image.image.name.endswith(".png"))
        self.assertEqual(PillowImage.open(queued_image.image).format, "PNG")

    def test_shows_photo_policy_text_in_photo_upload_page(self):
        upload_form_url = reverse("photo-upload", kwargs={"person_id": "2009"})
        response = self.app.get(upload_form_url, user=self.test_upload_user)
        self.assertContains(response, "Photo policy")

    def test_resize_image(self, *all_mock_requests):
        # Test that the image is less than or equal to 5MB after
        # upload and before saving to the database.
        image_size = os.path.getsize(self.xl_image_filename)
        self.assertGreater(image_size, 5000000)

        upload_form_file = reverse("photo-upload", kwargs={"person_id": "2009"})
        self.form_page_response = self.app.get(
            upload_form_file, user=self.test_upload_user
        )
        self.successful_get_oversized_image(*all_mock_requests)
        self.valid_form().submit()

        queued_image = QueuedImage.objects.filter(person_id=2009).last()
        image_size = queued_image.image.size
        self.assertLessEqual(image_size, 5000000)

    def test_rotate_image_from_file_upload(self, *all_mock_requests):
        pil_image = PillowImage.open(ROTATED_IMAGE_FILENAME)
        exif = pil_image.getexif()
        self.assertEqual(exif[274], 1)

        upload_form_file = reverse("photo-upload", kwargs={"person_id": "2009"})
        self.form_page_response = self.app.get(
            upload_form_file, user=self.test_upload_user
        )
        self.successful_get_rotated_image(*all_mock_requests)
        self.valid_form().submit()
        queued_image = QueuedImage.objects.filter(person_id=2009).last()
        pil_image = PillowImage.open(queued_image.image)
        exif = pil_image.getexif()
        self.assertEqual(exif._info, None)


@patch("moderation_queue.forms.requests")
@patch("moderation_queue.helpers.requests")
@override_settings(MEDIA_ROOT=TEST_MEDIA_ROOT)
class PhotoUploadURLTests(UK2015ExamplesMixin, WebTest):

    example_image_filename = EXAMPLE_IMAGE_FILENAME

    @classmethod
    def setUpClass(cls):
        super(PhotoUploadURLTests, cls).setUpClass()
        storage = FileSystemStorage()
        desired_storage_path = join("queued-images", "pilot.jpg")
        with open(cls.example_image_filename, "rb") as f:
            cls.storage_filename = storage.save(desired_storage_path, f)
        mkdir_p(TEST_MEDIA_ROOT)

    @classmethod
    def tearDownClass(cls):
        rmtree(TEST_MEDIA_ROOT)
        super(PhotoUploadURLTests, cls).tearDownClass()

    def setUp(self):
        super().setUp()
        PersonFactory.create(id=2009, name="Tessa Jowell")
        self.test_upload_user = User.objects.create_user(
            "john", "john@example.com", "notagoodpassword"
        )
        upload_form_url = reverse("photo-upload", kwargs={"person_id": "2009"})
        self.form_page_response = self.app.get(
            upload_form_url, user=self.test_upload_user
        )

    def get_and_head_methods(self, *all_mock_requests):
        return [
            getattr(mock_requests, attr)
            for mock_requests in all_mock_requests
            for attr in ("get", "head")
        ]

    def successful_get_image(self, *all_mock_requests, **kwargs):
        content_type = kwargs.get("content_type", "image/jpeg")
        headers = {"content-type": content_type}
        with open(self.example_image_filename, "rb") as image:
            image_data = image.read()
            for mock_method in self.get_and_head_methods(*all_mock_requests):
                setattr(
                    mock_method,
                    "return_value",
                    Mock(
                        status_code=200,
                        headers=headers,
                        # The chunk size is larger than the example
                        # image, so we don't need to worry about
                        # returning subsequent chunks.
                        iter_content=lambda **kwargs: [image_data],
                    ),
                )

    def unsuccessful_get_image(self, *all_mock_requests):
        for mock_method in self.get_and_head_methods(*all_mock_requests):
            setattr(mock_method, "return_value", Mock(status_code=404))

    def valid_form(self):
        form = self.form_page_response.forms["person-upload-photo-url"]
        form["image_url"] = "http://foo.com/bar.jpg"
        form["why_allowed_url"] = "copyright-assigned"
        form["justification_for_use_url"] = "I took this photo"
        return form

    def invalid_form(self):
        return self.form_page_response.forms["person-upload-photo-url"]

    def test_uploads_a_photo_from_a_url(self, *all_mock_requests):
        initial_count = QueuedImage.objects.all().count()
        self.successful_get_image(*all_mock_requests)
        self.valid_form().submit()
        final_count = QueuedImage.objects.all().count()
        self.assertEqual(final_count, initial_count + 1)

    def test_saves_the_form_values_correctly(self, *all_mock_requests):
        self.successful_get_image(*all_mock_requests)
        self.valid_form().submit()
        queued_image = QueuedImage.objects.all().last()
        self.assertEqual(queued_image.decision, "undecided")
        self.assertEqual(queued_image.why_allowed, "copyright-assigned")
        self.assertEqual(
            queued_image.justification_for_use, "I took this photo"
        )
        self.assertEqual(queued_image.person.id, 2009)
        self.assertEqual(queued_image.user, self.test_upload_user)

    def test_creates_a_logged_action(self, *all_mock_requests):
        initial_count = LoggedAction.objects.all().count()
        self.successful_get_image(*all_mock_requests)
        self.valid_form().submit()
        final_count = LoggedAction.objects.all().count()
        self.assertEqual(final_count, initial_count + 1)

    def test_image_converted_to_png(self, *all_mock_requests):
        self.assertEqual(
            PillowImage.open(self.example_image_filename).format, "JPEG"
        )
        self.successful_get_image(*all_mock_requests)
        self.valid_form().submit()
        queued_image = QueuedImage.objects.all().last()
        self.assertEqual(PillowImage.open(queued_image.image).format, "PNG")

    def test_loads_success_page_if_upload_was_successful(
        self, *all_mock_requests
    ):
        self.successful_get_image(*all_mock_requests)
        upload_response = self.valid_form().submit()
        self.assertEqual(upload_response.status_code, 302)
        split_location = urlsplit(upload_response.location)
        self.assertEqual(
            split_location.path, "/moderation/photo/upload/2009/success"
        )

    def test_fails_validation_if_image_does_not_exist(self, *all_mock_requests):
        self.unsuccessful_get_image(*all_mock_requests)
        upload_response = self.valid_form().submit()
        self.assertEqual(upload_response.status_code, 200)
        self.assertIn(
            "That URL produced an HTTP error status code: 404",
            upload_response.content.decode("utf-8"),
        )

    def test_fails_validation_if_image_has_wrong_content_type(
        self, *all_mock_requests
    ):
        self.successful_get_image(*all_mock_requests, content_type="text/html")
        upload_response = self.valid_form().submit()
        with open("/tmp/foo.html", "wb") as f:
            f.write(upload_response.content)
        self.assertEqual(upload_response.status_code, 200)
        self.assertIn(
            "This URL isn&#x27;t for an image - it had Content-Type: text/html",
            upload_response.content.decode("utf-8"),
        )

    def test_loads_upload_photo_page_if_form_is_invalid(
        self, *all_mock_requests
    ):
        self.successful_get_image(*all_mock_requests)
        upload_response = self.invalid_form().submit()
        self.assertContains(
            upload_response, "<h1>Upload a photo of Tessa Jowell</h1>"
        )

    def test_upload_size_restriction_works(self, *all_mock_requests):
        self.successful_get_image(*all_mock_requests)
        with self.assertRaises(ImageDownloadException) as context:
            download_image_from_url(
                "http://foo.com/bar.jpg", max_size_bytes=512
            )
        self.assertEqual(
            str(context.exception),
            "The image exceeded the maximum allowed size",
        )

    def test_convert_image_to_png_helper(self, *all_mock_requests):
        with open(EXAMPLE_IMAGE_FILENAME, "rb") as file:
            self.assertEqual(PillowImage.open(file).format, "JPEG")
            converted_image = convert_image_to_png(file)
            self.assertEqual(PillowImage.open(converted_image).format, "PNG")

    def test_download_image_from_url_helper(self, *all_mock_requests):
        self.successful_get_image(*all_mock_requests)
        image = download_image_from_url("http://foo.com/bar.jpg")
        self.assertEqual(PillowImage.open(image).format, "PNG")
