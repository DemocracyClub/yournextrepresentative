from django.test import TestCase
from django.urls import reverse


class TestSearchView(TestCase):
    def test_valid_postcode_regression(self):
        """
        Tests that a request with no query doesn't break - a regression for
        https://github.com/DemocracyClub/yournextrepresentative/issues/1305
        """

        req = self.client.get(reverse("person-search"))
        self.assertEqual(req.status_code, 200)
