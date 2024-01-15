import re

from candidates.tests.uk_examples import UK2015ExamplesMixin
from django_webtest import WebTest


class TestConstituencyDetailView(UK2015ExamplesMixin, WebTest):
    def setUp(self):
        super().setUp()

    def test_constituencies_page(self):
        # Just a smoke test to check that the page loads:
        response = self.app.get("/elections/parl.2015-05-07/")
        dulwich = response.html.find(
            "a", string=re.compile(r"Dulwich and West Norwood")
        )
        self.assertTrue(dulwich)
