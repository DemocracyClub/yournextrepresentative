# -*- coding: utf-8 -*-

from __future__ import unicode_literals

from django_webtest import WebTest

from .auth import TestUserMixin

from .factories import (
    CandidacyExtraFactory, PersonExtraFactory, PostExtraFactory
)
from .uk_examples import UK2015ExamplesMixin


class TestAreasOfTypeView(TestUserMixin, UK2015ExamplesMixin, WebTest):

    def setUpAll(self):
        super(TestAreasOfTypeView, self).setUp()
        person_extra = PersonExtraFactory.create(
            base__id='2009',
            base__name='Tessa Jowell'
        )
        CandidacyExtraFactory.create(
            base__person=person_extra.base,
            base__post=self.dulwich_post_extra.base,
            base__on_behalf_of=self.labour_party_extra.base,
            post_election=self.dulwich_post_extra_pee,
        )

        PostExtraFactory.create(
            elections=(self.election,),
            base__organization=self.commons,
            slug='65730',
            base__label='Member of Parliament for Aldershot',
            party_set=self.gb_parties,
        )

    def test_any_areas_of_type_page_without_login(self):
        response = self.app.get('/areas-of-type/WMC/')
        self.assertEqual(response.status_code, 301)

    def test_get_malformed_url(self):
        response = self.app.get(
            '/areas-of-type/3243452345/invalid',
            expect_errors=True
        )
        self.assertEqual(response.status_code, 301)


    def test_get_non_existent(self):
        response = self.app.get(
            '/areas-of-type/AAA/',
            expect_errors=True
        )
        self.assertEqual(response.status_code, 301)

    def test_posts_of_type(self):
        response = self.app.get(
            '/posts-of-type/WMC/',
            expect_errors=True
        )
        self.assertEqual(response.status_code, 200)
