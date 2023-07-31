from candidates.tests.uk_examples import UK2015ExamplesMixin
from django.test.utils import override_settings
from django_webtest import WebTest


class TestHomePageCTAs(UK2015ExamplesMixin, WebTest):
    @override_settings(FRONT_PAGE_CTA="BY_ELECTIONS")
    def test_by_elections(self):
        self.client.get("/")
