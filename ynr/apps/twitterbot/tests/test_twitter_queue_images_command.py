import re

from django.core.management import call_command
from django.test import TestCase
from mock import Mock, call, patch

from candidates.tests.auth import TestUserMixin
from candidates.tests.output import capture_output, split_output
from moderation_queue.models import QueuedImage
from moderation_queue.tests.paths import EXAMPLE_IMAGE_FILENAME
from people.models import PersonImage
from people.tests.factories import PersonFactory


@patch("twitterbot.management.commands.twitterbot_add_images_to_queue.requests")
@patch(
    "twitterbot.management.commands.twitterbot_add_images_to_queue.TwitterAPIData"
)
class TestTwitterImageQueueCommand(TestUserMixin, TestCase):

    maxDiff = None

    def setUp(self):
        self.image_filename = EXAMPLE_IMAGE_FILENAME
        with open(self.image_filename, "rb") as f:
            self.example_image_binary_data = f.read()

        self.p_no_images = PersonFactory.create(
            id="1", name="Person With No Existing Images"
        )
        self.p_no_images.tmp_person_identifiers.create(
            internal_identifier="1001", value_type="twitter_username"
        )

        p_existing_image = PersonFactory.create(
            id=2, name="Person With An Existing Image"
        )
        self.existing_undecided_image = p_existing_image.queuedimage_set.create(
            decision=QueuedImage.UNDECIDED, user=self.user
        )
        p_existing_image.tmp_person_identifiers.create(
            internal_identifier="1002", value_type="twitter_username"
        )

        self.p_only_rejected_in_queue = PersonFactory.create(
            id=3, name="Person With Only Rejected Images In The Queue"
        )
        self.existing_rejected_image = self.p_only_rejected_in_queue.queuedimage_set.create(
            decision=QueuedImage.REJECTED, user=self.user
        )
        self.p_only_rejected_in_queue.tmp_person_identifiers.create(
            internal_identifier="1003", value_type="twitter_username"
        )

        PersonFactory.create(id=4, name="Person With No Twitter User ID")

        self.p_accepted_image_in_queue = PersonFactory.create(
            id=5, name="Person With An Accepted Image In The Queue"
        )
        self.existing_accepted_image = self.p_accepted_image_in_queue.queuedimage_set.create(
            decision=QueuedImage.APPROVED, user=self.user
        )
        self.p_accepted_image_in_queue.tmp_person_identifiers.create(
            internal_identifier="1005", value_type="twitter_username"
        )
        # If they've had an image accepted, they'll probably have an
        # Image too, so create that:
        self.image_create_from_queue = PersonImage.objects.create_from_file(
            self.image_filename,
            "images/person-accepted.jpg",
            defaults={
                "person": self.p_accepted_image_in_queue,
                "source": "From Flickr, used as an example image",
                "copyright": "example-license",
                "uploading_user": self.user,
                "user_notes": "Here is a photo for you!",
            },
        )

        self.p_existing_image_but_none_in_queue = PersonFactory.create(
            id=6, name="Person With An Existing Image But None In The Queue"
        )
        self.p_existing_image_but_none_in_queue.tmp_person_identifiers.create(
            internal_identifier="1006", value_type="twitter_username"
        )
        self.image_create_from_queue = PersonImage.objects.create_from_file(
            self.image_filename,
            "images/person-existing-image.jpg",
            defaults={
                "person": self.p_existing_image_but_none_in_queue,
                "source": "From Flickr, used as an example image",
                "copyright": "example-license",
                "uploading_user": self.user,
                "user_notes": "Photo from their party page, say",
            },
        )
        self.existing_queued_image_ids = list(
            QueuedImage.objects.values_list("pk", flat=True)
        )

    def test_command(self, mock_twitter_data, mock_requests):

        mock_twitter_data.return_value.user_id_to_photo_url = {
            "1001": "https://pbs.twimg.com/profile_images/abc/foo.jpg",
            "1002": "https://pbs.twimg.com/profile_images/def/bar.jpg",
            "1003": "https://pbs.twimg.com/profile_images/ghi/baz.jpg",
            "1005": "https://pbs.twimg.com/profile_images/jkl/quux.jpg",
            "1006": "https://pbs.twimg.com/profile_images/mno/xyzzy.jpg",
        }

        mock_requests.get.return_value = Mock(
            content=self.example_image_binary_data, status_code=200
        )

        call_command("twitterbot_add_images_to_queue")

        new_queued_images = QueuedImage.objects.exclude(
            id__in=self.existing_queued_image_ids
        )

        self.assertEqual(
            mock_requests.get.mock_calls,
            [
                call("https://pbs.twimg.com/profile_images/mno/xyzzy.jpg"),
                call("https://pbs.twimg.com/profile_images/abc/foo.jpg"),
            ],
        )

        self.assertEqual(new_queued_images.count(), 2)
        newly_enqueued_a = new_queued_images.get(person=self.p_no_images)
        self.assertEqual(
            newly_enqueued_a.justification_for_use,
            "Auto imported from Twitter: https://twitter.com/intent/user?user_id=1001",
        )
        newly_enqueued_b = new_queued_images.get(
            person=self.p_existing_image_but_none_in_queue
        )
        self.assertEqual(
            newly_enqueued_b.justification_for_use,
            "Auto imported from Twitter: https://twitter.com/intent/user?user_id=1006",
        )

    def test_command_output(self, mock_twitter_data, mock_requests):
        mock_twitter_data.return_value.user_id_to_photo_url = {
            "1002": "https://pbs.twimg.com/profile_images/def/bar.jpg",
            "1003": "https://pbs.twimg.com/profile_images/ghi/baz.jpg",
            "1005": "https://pbs.twimg.com/profile_images/jkl/quux.jpg",
            "1006": "https://pbs.twimg.com/profile_images/mno/xyzzy.jpg",
        }

        mock_requests.get.return_value = Mock(
            content=self.example_image_binary_data, status_code=200
        )

        with capture_output() as (out, err):
            call_command("twitterbot_add_images_to_queue", verbosity=3)

        self.assertEqual(
            split_output(out),
            [
                "Considering adding a photo for Person With An Accepted "
                "Image In The Queue with Twitter user ID: 1005",
                "  That person already had an image in the queue, so skipping.",
                "Considering adding a photo for Person With An Existing "
                "Image with Twitter user ID: 1002",
                "  That person already had an image in the queue, so skipping.",
                "Considering adding a photo for Person With An Existing "
                "Image But None In The Queue with Twitter user ID: 1006",
                "  Adding that person's Twitter avatar to the moderation "
                "queue",
                "Considering adding a photo for Person With Only Rejected "
                "Images In The Queue with Twitter user ID: 1003",
                "  That person already had an image in the queue, so skipping.",
            ],
        )

        new_queued_images = QueuedImage.objects.exclude(
            id__in=self.existing_queued_image_ids
        )

        self.assertEqual(
            mock_requests.get.mock_calls,
            [call("https://pbs.twimg.com/profile_images/mno/xyzzy.jpg")],
        )

        self.assertEqual(new_queued_images.count(), 1)
        newly_enqueued = new_queued_images.get()
        self.assertEqual(
            newly_enqueued.person, self.p_existing_image_but_none_in_queue
        )
        self.assertEqual(
            newly_enqueued.justification_for_use,
            "Auto imported from Twitter: https://twitter.com/intent/user?user_id=1006",
        )

    def test_only_enqueue_from_200_status_code(
        self, mock_twitter_data, mock_requests
    ):

        mock_twitter_data.return_value.user_id_to_photo_url = {
            "1001": "https://pbs.twimg.com/profile_images/abc/foo.jpg",
            "1002": "https://pbs.twimg.com/profile_images/def/bar.jpg",
            "1003": "https://pbs.twimg.com/profile_images/ghi/baz.jpg",
            "1005": "https://pbs.twimg.com/profile_images/jkl/quux.jpg",
            "1006": "https://pbs.twimg.com/profile_images/mno/xyzzy.jpg",
        }

        def fake_get(url, *args, **kwargs):
            if url == "https://pbs.twimg.com/profile_images/abc/foo.jpg":
                return Mock(
                    content=self.example_image_binary_data, status_code=404
                )
            else:
                return Mock(
                    content=self.example_image_binary_data, status_code=200
                )

        mock_requests.get.side_effect = fake_get

        call_command("twitterbot_add_images_to_queue")

        new_queued_images = QueuedImage.objects.exclude(
            id__in=self.existing_queued_image_ids
        )

        self.assertEqual(
            mock_requests.get.mock_calls,
            [
                call("https://pbs.twimg.com/profile_images/mno/xyzzy.jpg"),
                call("https://pbs.twimg.com/profile_images/abc/foo.jpg"),
            ],
        )

        # Out of the two URLs of images that were downloaded, only one
        # had a 200 status code:
        self.assertEqual(new_queued_images.count(), 1)
        new_queued_images.get(person=self.p_existing_image_but_none_in_queue)
        newly_enqueued = new_queued_images.get()
        self.assertEqual(
            newly_enqueued.person, self.p_existing_image_but_none_in_queue
        )
        self.assertEqual(
            newly_enqueued.justification_for_use,
            "Auto imported from Twitter: https://twitter.com/intent/user?user_id=1006",
        )

    def test_only_enqueue_files_that_seem_to_be_images(
        self, mock_twitter_data, mock_requests
    ):

        mock_twitter_data.return_value.user_id_to_photo_url = {
            "1001": "https://pbs.twimg.com/profile_images/abc/foo.jpg",
            "1002": "https://pbs.twimg.com/profile_images/def/bar.jpg",
            "1003": "https://pbs.twimg.com/profile_images/ghi/baz.jpg",
            "1005": "https://pbs.twimg.com/profile_images/jkl/quux.jpg",
            "1006": "https://pbs.twimg.com/profile_images/mno/xyzzy.jpg",
        }

        def fake_get(url, *args, **kwargs):
            if url == "https://pbs.twimg.com/profile_images/abc/foo.jpg":
                return Mock(content=b"I am not an image.", status_code=200)
            else:
                return Mock(
                    content=self.example_image_binary_data, status_code=200
                )

        mock_requests.get.side_effect = fake_get

        with capture_output() as (out, err):
            call_command("twitterbot_add_images_to_queue")

        output_lines = split_output(out)
        self.assertEqual(len(output_lines), 1)
        self.assertTrue(
            re.search(r"^Ignoring a non-image file \S+$", output_lines[0])
        )

        new_queued_images = QueuedImage.objects.exclude(
            id__in=self.existing_queued_image_ids
        )

        self.assertEqual(
            mock_requests.get.mock_calls,
            [
                call("https://pbs.twimg.com/profile_images/mno/xyzzy.jpg"),
                call("https://pbs.twimg.com/profile_images/abc/foo.jpg"),
            ],
        )

        # Out of the two URLs of images that were downloaded, only one
        # had a 200 status code:
        self.assertEqual(new_queued_images.count(), 1)
        newly_enqueued = new_queued_images.get()
        self.assertEqual(
            newly_enqueued.person, self.p_existing_image_but_none_in_queue
        )
        self.assertEqual(
            newly_enqueued.justification_for_use,
            "Auto imported from Twitter: https://twitter.com/intent/user?user_id=1006",
        )
