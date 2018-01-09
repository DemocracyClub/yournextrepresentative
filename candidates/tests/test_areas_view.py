# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import re

from django_webtest import WebTest

from .auth import TestUserMixin

from .factories import (
    CandidacyExtraFactory, PersonExtraFactory, PostExtraFactory
)
from .uk_examples import UK2015ExamplesMixin

class TestAreasView(TestUserMixin, UK2015ExamplesMixin, WebTest):

    def test_any_area_page_without_login(self):
        response = self.app.get(
            '/areas/WMC--65808/dulwich-and-west-norwood',
            status=410
        )
        self.assertEqual(response.status_code, 410)


    def test_get_non_existent(self):
        response = self.app.get(
            '/areas/WMC--11111111/imaginary-constituency',
            expect_errors=True
        )
        self.assertEqual(response.status_code, 410)
