from datetime import timedelta

from django.test import TestCase
from django.utils.timezone import now
from frontend.models import SiteBanner


class TestSiteBanner(TestCase):
    def test_live(self):
        SiteBanner.objects.create(
            show_until=now() + timedelta(hours=1),
            message="testing site wide banner",
            published=True,
        )

        resp = self.client.get("/")
        self.assertContains(resp, "testing site wide banner")

    def test_only_newest_shown(self):
        SiteBanner.objects.create(
            show_until=now() + timedelta(hours=1),
            message="testing site wide banner 1",
            published=True,
        )

        SiteBanner.objects.create(
            show_until=now() + timedelta(hours=1),
            message="testing site wide banner 2",
            published=True,
        )

        resp = self.client.get("/")
        self.assertContains(resp, "testing site wide banner 2")
        self.assertNotContains(resp, "testing site wide banner 1")
