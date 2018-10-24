from django_webtest import WebTest
from candidates.tests.helpers import TmpMediaRootMixin

from candidates.tests.factories import PersonFactory, faker_factory
from people.models import PersonImage
from moderation_queue.tests.paths import EXAMPLE_IMAGE_FILENAME

from sorl.thumbnail import get_thumbnail


class TestPersonModels(TmpMediaRootMixin, WebTest):
    def test_get_display_image_url(self):
        person = PersonFactory(name=faker_factory.name())

        self.assertEqual(
            person.get_display_image_url(),
            "/static/candidates/img/blank-person.png",
        )

        pi = PersonImage.objects.create_from_file(
            EXAMPLE_IMAGE_FILENAME,
            "images/jowell-pilot.jpg",
            defaults={
                "person": person,
                "is_primary": True,
                "source": "Taken from Wikipedia",
                "copyright": "example-license",
                "user_notes": "A photo of Tessa Jowell",
            },
        )

        url = get_thumbnail(pi.image, "x64").url

        self.assertEqual(person.get_display_image_url(), url)
