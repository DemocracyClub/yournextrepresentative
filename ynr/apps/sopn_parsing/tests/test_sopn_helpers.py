from os.path import abspath, dirname, join

from django.test import TestCase

from sopn_parsing.helpers.text_helpers import clean_text

try:
    from sopn_parsing.helpers.pdf_helpers import SOPNDocument
except ImportError:
    pass


class TestSOPNHelpers(TestCase):
    def test_clean_text(self):
        text = "\n C andidates (Namés)"
        self.assertEqual(clean_text(text), "candidates")

    def test_sopn_document(self):
        example_doc_path = abspath(
            join(dirname(__file__), "data/sopn-berkeley-vale.pdf")
        )
        doc = SOPNDocument(open(example_doc_path, "rb"))

        self.assertSetEqual(
            doc.document_heading,
            {
                "following",
                "council",
                "of",
                "is",
                "statement",
                "district",
                "the",
                "for",
                "stroud",
                "persons",
                "nominated",
                "a",
                "election",
                "councillor",
                "vale",
                "berkeley",
                "on",
                "as",
                "name",
                "thursday",
                "candidate",
                "february",
                "28",
                "ashton",
                "2019",
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
        doc = SOPNDocument(open(example_doc_path, "rb"))

        self.assertEqual(len(doc.pages), 9)

        na_wards = doc.get_pages_by_ward_name("north antrim")

        self.assertEqual(len(na_wards), 5)
        self.assertEqual(na_wards[0].page_number, 5)
