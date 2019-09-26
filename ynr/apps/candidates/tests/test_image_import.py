import hashlib

from django.contrib.contenttypes.models import ContentType
from django.test import TestCase

import people.tests.factories
from moderation_queue.tests.paths import EXAMPLE_IMAGE_FILENAME
from people.models import PersonImage

from .auth import TestUserMixin


def get_file_md5sum(filename):
    with open(filename, "rb") as f:
        return hashlib.md5(f.read()).hexdigest()


class TestImageImport(TestUserMixin, TestCase):
    def setUp(self):
        self.person = people.tests.factories.PersonFactory.create(name="Alex")
        self.org_ct = ContentType.objects.get_for_model(self.person)
        self.image_filename = EXAMPLE_IMAGE_FILENAME

    def test_import_new_image(self):
        md5sum = get_file_md5sum(self.image_filename)
        self.assertEqual(0, self.person.images.count())
        PersonImage.objects.update_or_create_from_file(
            self.image_filename,
            "images/imported.jpg",
            self.person,
            defaults={
                "md5sum": md5sum,
                "copyright": "example-license",
                "uploading_user": self.user,
                "user_notes": "Here's an image...",
                "is_primary": True,
                "source": "Found on the candidate's Flickr feed",
            },
        )
        self.assertEqual(1, self.person.images.count())
        # This refetches the object from the database so we don't get
        # ORM-cached data:
        updated_labour = self.person.images.first()
        self.assertEqual(updated_labour.copyright, "example-license")
        self.assertEqual(updated_labour.uploading_user, self.user)
        self.assertEqual(updated_labour.user_notes, "Here's an image...")
        self.assertEqual(
            updated_labour.source, "Found on the candidate's Flickr feed"
        )
        self.assertTrue(updated_labour.is_primary)

    def test_update_imported_image(self):
        md5sum = get_file_md5sum(self.image_filename)
        self.assertEqual(0, self.person.images.count())
        PersonImage.objects.update_or_create_from_file(
            self.image_filename,
            "images/imported.jpg",
            self.person,
            defaults={
                "md5sum": md5sum,
                "copyright": "example-license",
                "uploading_user": self.user,
                "user_notes": "Here's an image...",
                "is_primary": True,
                "source": "Found on the candidates Flickr feed",
            },
        )
        self.assertEqual(1, self.person.images.count())
        # Now try to update that image:
        PersonImage.objects.update_or_create_from_file(
            self.image_filename,
            "images/imported.jpg",
            self.person,
            defaults={
                "md5sum": md5sum,
                "copyright": "another-license",
                "uploading_user": self.user_who_can_merge,
                "user_notes": "The classic image...",
                "is_primary": True,
                "source": "The same image from the Flickr feed",
            },
        )
        self.assertEqual(1, self.person.images.count())
        # This refetches the object from the database so we don't get
        # ORM-cached data:
        updated_labour = self.person.images.first()
        self.assertEqual(updated_labour.copyright, "another-license")
        self.assertEqual(updated_labour.uploading_user, self.user_who_can_merge)
        self.assertEqual(updated_labour.user_notes, "The classic image...")
        self.assertEqual(
            updated_labour.source, "The same image from the Flickr feed"
        )
        self.assertTrue(updated_labour.is_primary)
