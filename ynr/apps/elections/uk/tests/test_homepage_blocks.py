# -*- coding: utf-8 -*-

from django_webtest import WebTest

from django.conf import settings
from django.test.utils import override_settings

from candidates.tests.uk_examples import UK2015ExamplesMixin


class TestHomePageCTAs(UK2015ExamplesMixin, WebTest):
    @override_settings(FRONT_PAGE_CTA="BY_ELECTIONS")
    def test_by_elections(self):
        self.client.get("/")
