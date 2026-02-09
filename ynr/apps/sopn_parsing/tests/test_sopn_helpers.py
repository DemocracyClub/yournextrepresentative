import contextlib
import json
import os
from os.path import abspath, dirname, join
from pathlib import Path
from unittest import skipIf
from unittest.mock import PropertyMock

import pytest
from candidates.tests.factories import (
    BallotPaperFactory,
    ElectionFactory,
    OrganizationFactory,
)
from candidates.tests.uk_examples import UK2015ExamplesMixin
from django.core.files import File
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from mock import Mock
from official_documents.models import BallotSOPN, ElectionSOPN
from sopn_parsing.helpers.text_helpers import NoTextInDocumentError, clean_text
from sopn_parsing.helpers.textract_helpers import (
    get_extractor_class,
)
from sopn_parsing.models import AWSTextractParsedSOPN
from sopn_parsing.tests import should_skip_pdf_tests
from textractor.entities.lazy_document import LazyDocument

with contextlib.suppress(ImportError):
    from official_documents.extract_pages import ElectionSOPNDocument


class TestSOPNHelpers(UK2015ExamplesMixin, TestCase):
    def test_clean_text(self):
        text = "\n C andidates (Namés)"
        self.assertEqual(clean_text(text), "candidates")

    def test_clean_text_removes_digits(self):
        for text in [
            "enwr ymgeisydd candidate name5",
            "enwr ymgeisydd candidate name 5",
            "enwr ymgeisydd candidate name\n5",
        ]:
            with self.subTest(msg=text):
                self.assertEqual(
                    clean_text(text), "enwr ymgeisydd candidate name"
                )

    def test_empty_documents(self):
        example_doc_path = abspath(
            join(dirname(__file__), "data/sopn-berkeley-vale.pdf")
        )
        with open(example_doc_path, "rb") as f:
            election_sopn = ElectionSOPN.objects.create(
                election=self.local_election,
                uploaded_file=SimpleUploadedFile("sopn.pdf", f.read()),
            )
            doc = ElectionSOPNDocument(
                election_sopn=election_sopn,
            )
        doc.heading = {"reason", "2019", "a", "election", "the", "labour"}
        self.assertEqual(len(doc.pages), 1)
        self.assertEqual(doc.blank_doc, False)
        self.assertRaises(NoTextInDocumentError)

    @skipIf(should_skip_pdf_tests(), "Required PDF libs not installed")
    def test_sopn_document(self):
        example_doc_path = abspath(
            join(dirname(__file__), "data/sopn-berkeley-vale.pdf")
        )
        with open(example_doc_path, "rb") as f:
            election_sopn = ElectionSOPN.objects.create(
                election=self.local_election,
                uploaded_file=SimpleUploadedFile("sopn.pdf", f.read()),
            )
            doc = ElectionSOPNDocument(election_sopn=election_sopn)
        self.assertSetEqual(
            doc.document_heading_set,
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
    def test_single_page_sopn(self):
        example_doc_path = abspath(
            join(dirname(__file__), "data/sopn-berkeley-vale.pdf")
        )
        ballot = BallotPaperFactory(
            ballot_paper_id="local.stroud.berkeley-vale.by.2019-02-28"
        )
        with open(example_doc_path, "rb") as f:
            election_sopn = ElectionSOPN(
                election=ballot.election,
                source_url="http://example.com/strensall",
            )
            election_sopn.uploaded_file.save(name="sopn.pdf", content=f)
            election_sopn.save()

            document_obj = ElectionSOPNDocument(election_sopn=election_sopn)
            self.assertEqual(len(document_obj.pages), 1)

            document_obj.match_all_pages()
            ballot.refresh_from_db()
            self.assertEqual(ballot.sopn.relevant_pages, "all")

    @skipIf(should_skip_pdf_tests(), "Required PDF libs not installed")
    def test_multipage_doc(self):
        """
        Uses the example of a multipage PDF which contains SOPN's for two
        ballots.
        Creates the ballots, then parses the document, and checks that the
        correct pages have been assigned to the BallotSOPN object
        related to the ballot.
        """
        example_doc_path = abspath(
            join(dirname(__file__), "data/NI-Assembly-Election-2016.pdf")
        )
        election = ElectionFactory(
            slug="nia.2016-05-05", election_date="2016-05-05"
        )
        organization = OrganizationFactory(slug="nia:nia")
        mid_ulster = BallotPaperFactory(
            ballot_paper_id="nia.mid-ulster.2016-05-05",
            election=election,
            post__label="mid ulster",
            post__organization=organization,
        )
        north_antrim = BallotPaperFactory(
            ballot_paper_id="nia.north-antrim.2016-05-05",
            election=election,
            post__label="north antrim",
            post__organization=organization,
        )
        with open(example_doc_path, "rb") as f:
            election_sopn = ElectionSOPN(
                election=election,
                source_url="http://example.com",
            )
            election_sopn.uploaded_file.save(name="sopn.pdf", content=f)
            election_sopn.save()

            document_obj = ElectionSOPNDocument(election_sopn=election_sopn)
        self.assertEqual(len(document_obj.pages), 9)
        document_obj.match_all_pages()

        self.assertEqual(mid_ulster.sopn.relevant_pages, "0,1,2,3")
        self.assertEqual(north_antrim.sopn.relevant_pages, "4,5,6,7,8")

    @skipIf(should_skip_pdf_tests(), "Required PDF libs not installed")
    def test_document_with_identical_headers(self):
        """
        Uses an example PDF where the two headers are identical to check that
        the second page is recognised as a continuation of the previous page
        """
        sopn_pdf = abspath(
            join(dirname(__file__), "data/local.york.strensall.2019-05-02.pdf")
        )
        strensall = BallotPaperFactory(
            ballot_paper_id="local.york.strensall.2019-05-02",
            post__label="Strensall",
        )
        with open(sopn_pdf, "rb") as f:
            sopn_file = File(f)
            election_sopn = ElectionSOPN(
                election=strensall.election,
                source_url="http://example.com/strensall",
            )
            election_sopn.uploaded_file.save(name="sopn.pdf", content=sopn_file)
            election_sopn.save()

            document_obj = ElectionSOPNDocument(election_sopn=election_sopn)
        self.assertEqual(len(document_obj.pages), 2)

        document_obj.match_all_pages()
        self.assertEqual(strensall.sopn.relevant_pages, "all")


@pytest.fixture
def aws_credentials():
    """Mocked AWS Credentials for moto."""
    os.environ["AWS_ACCESS_KEY_ID"] = "testing"
    os.environ["AWS_SECRET_ACCESS_KEY"] = "testing"
    os.environ["AWS_SECURITY_TOKEN"] = "testing"
    os.environ["AWS_SES SION_TOKEN"] = "testing"


@pytest.fixture
def textract_sopn_helper(db):
    sopn_pdf_path = (
        Path(__file__).parent / "data/local.york.strensall.2019-05-02.pdf"
    )
    with sopn_pdf_path.open("rb") as sopn_file:
        ballot_sopn = BallotSOPN.objects.create(
            ballot=BallotPaperFactory(
                ballot_paper_id="local.york.strensall.2019-05-02"
            ),
            uploaded_file=SimpleUploadedFile("sopn.pdf", sopn_file.read()),
        )
    yield get_extractor_class()(
        ballot_sopn=ballot_sopn, upload_path="s3://fake_bucket/"
    )


def load_json_fixture(path):
    with open(path, "r") as f:
        return json.load(f)


@pytest.fixture
def completed_analysis():
    return load_json_fixture(
        "ynr/apps/sopn_parsing/tests/data/sample_textract_token_test.json"
    )


@pytest.fixture
def get_document_analysis_json():
    return load_json_fixture(
        "ynr/apps/sopn_parsing/tests/data/sample_textract_response.json"
    )


@pytest.fixture
def failed_analysis():
    return load_json_fixture(
        "ynr/apps/sopn_parsing/tests/data/sample_textract_token_test_failure.json"
    )


@pytest.fixture
def get_mock_document():
    def _get_doc(json_response):
        doc = LazyDocument
        doc.response = PropertyMock(return_value=json_response)
        doc._response = json_response
        doc.job_id = "1234"
        doc.images = []
        doc._pages = PropertyMock(return_value=[])
        doc.pages = PropertyMock(return_value=[])
        return doc

    return _get_doc


def test_start_detection(
    textract_sopn_helper, get_mock_document, get_document_analysis_json
):
    mock_document = get_mock_document(get_document_analysis_json)
    mock_document_analysis = Mock()
    mock_document_analysis.return_value = mock_document
    textract_sopn_helper.textract_start_document_analysis = (
        mock_document_analysis
    )

    textract_result = textract_sopn_helper.start_detection()
    # start_detection should return a job id and the default status of a textract response
    # because it hasn't been updated yet.
    assert textract_result.job_id == "1234"
    assert textract_result.status == "NOT_STARTED"


def test_update_job_status_succeeded(
    textract_sopn_helper, get_document_analysis_json, get_mock_document
):
    ballot_sopn = textract_sopn_helper.ballot_sopn
    AWSTextractParsedSOPN.objects.create(
        sopn=ballot_sopn,
        job_id="1234",
        raw_data="",
        status="NOT_STARTED",
    )

    mock_document = get_mock_document(get_document_analysis_json)
    mock_get_result = Mock()
    mock_get_result.return_value = mock_document
    textract_sopn_helper.extractor.get_result = mock_get_result
    textract_sopn_helper.extractor._get_document_images_from_path = lambda x: []

    textract_sopn_helper.update_job_status(blocking=True)
    assert ballot_sopn.awstextractparsedsopn.status == "SUCCEEDED"


def test_update_job_status_failed(
    textract_sopn_helper, failed_analysis, get_mock_document
):
    ballot_sopn = textract_sopn_helper.ballot_sopn
    AWSTextractParsedSOPN.objects.create(
        sopn=ballot_sopn,
        job_id="1234",
        raw_data="",
        status="NOT_STARTED",
    )

    mock_document = get_mock_document(failed_analysis)
    mock_get_result = Mock()
    mock_get_result.return_value = mock_document
    textract_sopn_helper.extractor.get_result = mock_get_result
    textract_sopn_helper.extractor._get_document_images_from_path = lambda x: []

    textract_sopn_helper.update_job_status(blocking=True)
    ballot_sopn.awstextractparsedsopn.refresh_from_db()
    assert ballot_sopn.awstextractparsedsopn.status == "FAILED"
