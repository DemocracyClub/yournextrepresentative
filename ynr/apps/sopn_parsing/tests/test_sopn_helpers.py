from os.path import abspath, dirname, join

from django.test import TestCase
from unittest import skipIf

from sopn_parsing.helpers.text_helpers import clean_text
from sopn_parsing.tests import should_skip_pdf_tests

try:
    from sopn_parsing.helpers.pdf_helpers import SOPNDocument
except ImportError:
    pass


class TestSOPNHelpers(TestCase):
    def test_clean_text(self):
        text = "\n C andidates (Namés)"
        self.assertEqual(clean_text(text), "candidates")

    @skipIf(should_skip_pdf_tests(), "Required PDF libs not installed")
    def test_sopn_document(self):
        example_doc_path = abspath(
            join(dirname(__file__), "data/sopn-berkeley-vale.pdf")
        )

        # TODO: pass in a list of documents from get_all_documents_with_source()
        doc = SOPNDocument(open(example_doc_path, "rb"))
        self.assertSetEqual(
            doc.document_heading,
            {
                # Header
                "the",
                "statement",
                "of",
                "persons",
                "nominated",
                "for",
                "stroud",
                "district",
                "berkeley",
                "vale",
                "council",
                "on",
                "thursday",
                "february",
                "28",
                "2019",
                # table headers
                "candidate",
                "name",
                "description",
                "proposer",
                "reason",
                "why",
                "no",
                "longer",
                "(if",
                "any)",
                # candidates
                "simpson",
                "jane",
                "eleanor",
                "liz",
                "ashton",
                "lindsey",
                "simpson",
                "labour",
                "green",
                "party",
                # More words here?
                "election",
                "a",
                "councillor",
                "following",
                "is",
                "as",
            },
        )

        self.assertEqual(len(doc.pages), 1)
        self.assertEqual(
            doc.get_pages_by_ward_name("berkeley")[0].page_number, 1
        )

    @skipIf(should_skip_pdf_tests(), "Required PDF libs not installed")
    def test_multipage_doc(self):

        example_doc_path = abspath(
            join(dirname(__file__), "data/NI-Assembly-Election-2016.pdf")
        )
        # TODO: pass in a list of documents from get_all_documents_with_source()
        doc = SOPNDocument(open(example_doc_path, "rb"))
        self.assertEqual(len(doc.pages), 9)
        na_wards = doc.get_pages_by_ward_name("north antrim")
        self.assertEqual(len(na_wards), 5)
        self.assertEqual(na_wards[0].page_number, 5)

        doc = SOPNDocument(open(example_doc_path, "rb"))
        ulster_wards = doc.get_pages_by_ward_name("ulster")
        self.assertEqual(len(ulster_wards), 4)
        self.assertEqual(ulster_wards[0].page_number, 1)
