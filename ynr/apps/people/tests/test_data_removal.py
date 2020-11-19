import json

from django_webtest import WebTest

import people.tests.factories
from candidates.tests.auth import TestUserMixin
from candidates.tests.uk_examples import UK2015ExamplesMixin
from people.data_removal_helpers import DataRemover
from people.tests.test_merge_view import EXAMPLE_VERSIONS


class TestDataRemoval(TestUserMixin, UK2015ExamplesMixin, WebTest):
    def setUp(self):
        self.maxDiff = None
        super().setUp()
        # Create Tessa Jowell (the primary person)
        self.person = people.tests.factories.PersonFactory.create(
            id=2009,
            name="Tessa Jowell",
            gender="female",
            honorific_suffix="DBE",
            versions=EXAMPLE_VERSIONS,
        )

    def test_data_removal_collect(self):
        dr = DataRemover(self.person)
        self.assertDictEqual(
            dr.collect(),
            {
                "PhotoCheck": [],
                "VersionHistoryCheck": [
                    {"title": "gender", "description": "female"},
                    {
                        "title": "email",
                        "description": "jowell@example.com\n\ttessa.jowell@example.com",
                    },
                    {
                        "title": "homepage_url",
                        "description": "http://example.org/tessajowell",
                    },
                    {"title": "birth_date", "description": "1947-09-17"},
                ],
            },
        )

    def test_cant_remove_before_check(self):
        dr = DataRemover(self.person)
        with self.assertRaises(ValueError) as ve:
            dr.remove()
        exception = str(ve.exception)
        self.assertEqual(
            exception, "Can't remove data without calling collect first"
        )

    def test_remove_correct_data(self):
        dr = DataRemover(self.person)
        dr.collect()
        dr.remove()
        self.person.refresh_from_db()
        self.assertEqual(
            json.loads(self.person.versions),
            [
                {
                    "username": "symroe",
                    "information_source": "Just adding example data",
                    "ip": "127.0.0.1",
                    "version_id": "35ec2d5821176ccc",
                    "timestamp": "2014-10-28T14:32:36.835429",
                    "data": {
                        "name": "Tessa Jowell",
                        "other_names": [
                            {"name": "Tessa Palmer", "note": "maiden name"}
                        ],
                        "id": "2009",
                        "honorific_suffix": "DBE",
                        "twitter_username": "",
                        "candidacies": {
                            "parl.65808.2010-05-06": {"party": "PP53"},
                            "parl.65808.2015-05-07": {"party": "PP53"},
                        },
                        "gender": "<DELETED>",
                        "homepage_url": "",
                        "birth_date": None,
                        "wikipedia_url": "https://en.wikipedia.org/wiki/Tessa_Jowell",
                        "email": "<DELETED>",
                    },
                },
                {
                    "username": "mark",
                    "information_source": "An initial version",
                    "ip": "127.0.0.1",
                    "version_id": "5469de7db0cbd155",
                    "timestamp": "2014-10-01T15:12:34.732426",
                    "data": {
                        "name": "Tessa Jowell",
                        "id": "2009",
                        "twitter_username": "",
                        "candidacies": {
                            "parl.65808.2010-05-06": {"party": "PP53"}
                        },
                        "homepage_url": "<DELETED>",
                        "birth_date": "<DELETED>",
                        "wikipedia_url": "",
                        "email": "<DELETED>",
                    },
                },
            ],
        )
