from os.path import abspath, dirname, join

from django.test import TestCase
from unittest import skipIf

from sopn_parsing.helpers.text_helpers import clean_text
from sopn_parsing.helpers.extract_pages import get_all_documents_with_source
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
        all_documents_with_source = get_all_documents_with_source(
            example_doc_path
        )
        doc = SOPNDocument(
            open(example_doc_path, "rb"), all_documents_with_source
        )
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

    @skipIf(should_skip_pdf_tests(), "Required PDF libs not installed")
    def test_multipage_doc(self):
        example_doc_path = abspath(
            join(dirname(__file__), "data/NI-Assembly-Election-2016.pdf")
        )

        all_documents_with_source = get_all_documents_with_source(
            example_doc_path
        )
        doc = SOPNDocument(
            open(example_doc_path, "rb"), all_documents_with_source
        )
        self.assertEqual(len(doc.pages), 9)

        for doc_info in doc.match_all_pages():
            self.assertEqual(doc_info[0], doc.pages[0])
            self.assertEqual(doc_info[1], "1,2")
