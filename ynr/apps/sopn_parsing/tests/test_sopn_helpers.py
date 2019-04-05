from os.path import abspath, join, dirname
from unittest import skipIf, skip

from django.test import TestCase

from sopn_parsing.helpers.text_helpers import clean_text
from sopn_parsing.tests import should_skip_pdf_tests

try:
    from sopn_parsing.helpers.pdf_helpers import SOPNDocument
except ImportError:
    pass


@skip("Fix backend storage in tests")
@skipIf(should_skip_pdf_tests(), "Required PDF libs not installed")
class TestSOPNHelpers(TestCase):
    def test_clean_text(self):
        text = "\n C andidates (Namés)"
        self.assertEqual(clean_text(text), "candidates")

    def test_sopn_document(self):
        example_doc_path = abspath(
            join(dirname(__file__), "data/sopn-berkeley-vale.pdf")
        )
        doc = SOPNDocument(example_doc_path)
        self.assertSetEqual(
            doc.document_heading,
            {
                "",
                "william",
                "following",
                "february",
                "council",
                "lindsey",
                "mike",
                "of",
                "is",
                "name",
                "statement",
                "candidate",
                "district",
                "the",
                "little",
                "vale",
                "moscow,",
                "2019",
                "jane",
                "as",
                "willetts",
                "stayte",
                "on",
                "for",
                "berkeley",
                "stroud",
                "ashton",
                "green",
                "28",
                "thursday",
                "edward",
                "berrycr",
                "persons",
                "liz",
                "nominated",
                "a",
                "thomas",
                "home",
                "address",
                "election",
                "councillor",
            },
        )

        self.assertEqual(len(doc.pages), 1)
        self.assertEqual(
            doc.get_pages_by_ward_name("berkeley")[0].page_number, 1
        )

    def test_multipage_doc(self):
        example_doc_path = abspath(
            join(dirname(__file__), "data/NI-Assembly-Election-2016.pdf")
        )
        doc = SOPNDocument(example_doc_path)
        self.assertEqual(len(doc.pages), 9)

        na_wards = doc.get_pages_by_ward_name("north antrim")

        self.assertEqual(len(na_wards), 5)
        self.assertEqual(na_wards[0].page_number, 5)
