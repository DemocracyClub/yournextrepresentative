"""
Basic smoke tests for OfficialDocument model
"""


from candidates.tests.factories import (
    ElectionFactory,
    ParliamentaryChamberFactory,
    PostFactory,
)
from django.test import TestCase
from official_documents.models import BallotSOPN


class TestModels(TestCase):
    def setUp(self):
        election = ElectionFactory.create(
            slug="parl.2015-05-07", name="2015 General Election"
        )
        commons = ParliamentaryChamberFactory.create()
        self.post = PostFactory.create(
            elections=(election,),
            organization=commons,
            slug="dulwich-and-west-norwood",
            label="Member of Parliament for Dulwich and West Norwood",
        )
        self.ballot = self.post.ballot_set.get()

    def test_unicode(self):
        doc = BallotSOPN(ballot=self.ballot, source_url="http://example.com/")

        self.assertEqual(
            str(doc),
            "parl.dulwich-and-west-norwood.2015-05-07 (http://example.com/)",
        )

    def test_relevant_pages(self):
        doc = BallotSOPN(ballot=self.ballot, source_url="http://example.com/")
        self.assertIsNone(doc.first_page_number)
        self.assertIsNone(doc.last_page_number)

        doc.relevant_pages = "all"

        self.assertIsNone(doc.first_page_number)
        self.assertIsNone(doc.last_page_number)

        doc.relevant_pages = "3,4,5,6,7"

        self.assertEqual(doc.first_page_number, 3)
        self.assertEqual(doc.last_page_number, 7)

        doc.relevant_pages = "5,6,7,1"

        self.assertEqual(doc.first_page_number, 1)
        self.assertEqual(doc.last_page_number, 7)
