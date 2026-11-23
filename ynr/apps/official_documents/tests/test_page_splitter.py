from io import BytesIO
from unittest.mock import patch

from candidates.models import Ballot
from candidates.tests.factories import (
    BallotPaperFactory,
    ElectionFactory,
    PostFactory,
)
from candidates.tests.uk_examples import UK2015ExamplesMixin
from django.core.files.base import ContentFile
from django.db import connection
from django.test import TestCase
from django.test.utils import CaptureQueriesContext
from official_documents.extract_pages import (
    ElectionSOPNPageSplitter,
    PDFProcessingError,
)
from official_documents.models import BallotSOPN, ElectionSOPN
from pypdf import PdfReader, PdfWriter
from pypdf.errors import DependencyError, PdfReadError


class ElectionSOPNPageSplitterTestCase(UK2015ExamplesMixin, TestCase):
    def setUp(self):
        election = ElectionFactory.create(
            slug="arse",
            name="2015 General Election",
            current=True,
        )
        BallotPaperFactory(
            election=election,
            post=PostFactory(label="Constituency 1", organization=self.commons),
            ballot_paper_id="ballot1",
        )
        BallotPaperFactory(
            election=election,
            post=PostFactory(label="Constituency 2", organization=self.commons),
            ballot_paper_id="ballot2",
        )
        self.election_sopn = ElectionSOPN.objects.create(
            election=election,
            uploaded_file=ContentFile(
                self.create_sample_pdf(), name="test_sopn.pdf"
            ),
        )

    def create_sample_pdf(self):
        writer = PdfWriter()

        for _ in range(3):
            writer.add_blank_page(width=612, height=792)

        buffer = BytesIO()
        writer.write(buffer)
        buffer.seek(0)

        return buffer.read()

    def test_raises_pdf_read_error_for_non_pdf(self):
        non_pdf_sopn = ElectionSOPN.objects.create(
            election=self.election_sopn.election,
            uploaded_file=ContentFile(b"not a pdf", name="test_sopn.txt"),
        )
        with self.assertRaises(PdfReadError):
            ElectionSOPNPageSplitter(non_pdf_sopn, {"ballot1": [0]})

    def test_dependency_error_raises_pdf_processing_error(self):
        ballot_to_pages = {"ballot1": [0]}
        splitter = ElectionSOPNPageSplitter(self.election_sopn, ballot_to_pages)
        with (
            patch.object(
                PdfWriter,
                "add_page",
                side_effect=DependencyError("missing dependency"),
            ),
            self.assertRaises(PDFProcessingError),
        ):
            splitter.split()

    def test_unknown_ballot_raises_does_not_exist(self):
        splitter = ElectionSOPNPageSplitter(
            self.election_sopn, {"ballot1": [0], "nope": [1]}
        )
        with self.assertRaises(Ballot.DoesNotExist):
            splitter.split()
        self.assertFalse(BallotSOPN.objects.exists())

    def test_split_fetches_ballots_in_one_query(self):
        splitter = ElectionSOPNPageSplitter(
            self.election_sopn, {"ballot1": [0], "ballot2": [1, 2]}
        )
        with CaptureQueriesContext(connection) as queries:
            splitter.split(parse_ballots=False)
        ballot_queries = [
            q
            for q in queries.captured_queries
            if 'FROM "candidates_ballot"' in q["sql"]
            and "ballot_paper_id" in q["sql"]
        ]
        self.assertEqual(len(ballot_queries), 1)

    def test_split_pages(self):
        ballot_to_pages = {
            "ballot1": [0],
            "ballot2": [1, 2],
        }
        splitter = ElectionSOPNPageSplitter(self.election_sopn, ballot_to_pages)
        splitter.split()

        ballot_sopns = BallotSOPN.objects.filter(
            election_sopn=self.election_sopn
        )
        self.assertEqual(ballot_sopns.count(), 2)

        bs1 = ballot_sopns.get(ballot__ballot_paper_id="ballot1")
        reader = PdfReader(bs1.uploaded_file.open())
        self.assertEqual(len(reader.pages), 1)

        bs2 = ballot_sopns.get(ballot__ballot_paper_id="ballot2")
        reader = PdfReader(bs2.uploaded_file.open())
        self.assertEqual(len(reader.pages), 2)
