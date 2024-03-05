import contextlib
import json
import os
from os.path import abspath, dirname, join
from pathlib import Path
from unittest import skipIf

import pytest
from candidates.tests.factories import (
    BallotPaperFactory,
    ElectionFactory,
    OrganizationFactory,
)
from django.core.files import File
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from mock import Mock, patch
from official_documents.models import OfficialDocument
from sopn_parsing.helpers.extract_pages import (
    TextractSOPNHelper,
    TextractSOPNParsingHelper,
)
from sopn_parsing.helpers.text_helpers import NoTextInDocumentError, clean_text
from sopn_parsing.models import AWSTextractParsedSOPN
from sopn_parsing.tests import should_skip_pdf_tests

with contextlib.suppress(ImportError):
    from sopn_parsing.helpers.pdf_helpers import SOPNDocument


class TestSOPNHelpers(TestCase):
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
            sopn_file = File(f)
            doc = SOPNDocument(
                file=sopn_file,
                source_url="http://example.com",
                election_date="2019-02-28",
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
            sopn_file = File(f)
            doc = SOPNDocument(
                sopn_file,
                source_url="http://example.com",
                election_date="2022-02-28",
            )
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
            sopn_file = File(f)
            official_document = OfficialDocument(
                ballot=ballot,
                source_url="http://example.com/strensall",
                document_type=OfficialDocument.NOMINATION_PAPER,
            )
            official_document.uploaded_file.save(
                name="sopn.pdf", content=sopn_file
            )
            official_document.save()
            self.assertEqual(official_document.relevant_pages, "")

            document_obj = SOPNDocument(
                file=sopn_file,
                source_url="http://example.com/strensall",
                election_date=ballot.election.election_date,
            )
            self.assertEqual(len(document_obj.pages), 1)

            document_obj.match_all_pages()
            self.assertEqual(ballot.sopn.relevant_pages, "all")

    @skipIf(should_skip_pdf_tests(), "Required PDF libs not installed")
    def test_multipage_doc(self):
        """
        Uses the example of a multipage PDF which contains SOPN's for two
        ballots.
        Creates the ballots, then parses the document, and checks that the
        correct pages have been assigned to the OfficialDocument object
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
            sopn_file = File(f)
            # assign the same PDF to both ballots with the same source URL
            for ballot in [north_antrim, mid_ulster]:
                official_document = OfficialDocument(
                    ballot=ballot,
                    source_url="http://example.com",
                    document_type=OfficialDocument.NOMINATION_PAPER,
                )
                official_document.uploaded_file.save(
                    name="sopn.pdf", content=sopn_file
                )
                official_document.save()
                self.assertEqual(official_document.relevant_pages, "")

            document_obj = SOPNDocument(
                file=sopn_file,
                source_url="http://example.com",
                election_date=election.election_date,
            )
        self.assertEqual(len(document_obj.pages), 9)
        document_obj.match_all_pages()

        self.assertEqual(mid_ulster.sopn.relevant_pages, "1,2,3,4")
        self.assertEqual(north_antrim.sopn.relevant_pages, "5,6,7,8,9")

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
            official_document = OfficialDocument(
                ballot=strensall,
                source_url="http://example.com/strensall",
                document_type=OfficialDocument.NOMINATION_PAPER,
            )
            official_document.uploaded_file.save(
                name="sopn.pdf", content=sopn_file
            )
            official_document.save()
            self.assertEqual(official_document.relevant_pages, "")

            document_obj = SOPNDocument(
                file=sopn_file,
                source_url="http://example.com/strensall",
                election_date=strensall.election.election_date,
            )
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
        official_document = OfficialDocument.objects.create(
            ballot=BallotPaperFactory(
                ballot_paper_id="local.york.strensall.2019-05-02"
            ),
            document_type=OfficialDocument.NOMINATION_PAPER,
            uploaded_file=SimpleUploadedFile("sopn.pdf", sopn_file.read()),
        )
    yield TextractSOPNHelper(official_document=official_document)


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


def test_start_detection(textract_sopn_helper, get_document_analysis_json):
    with patch(
        "sopn_parsing.helpers.extract_pages.TextractSOPNHelper.textract_start_document_analysis"
    ) as mock_textract_start_document_analysis:
        mock_textract_start_document_analysis.return_value = {"JobId": "1234"}
        textract_result = textract_sopn_helper.start_detection()
    # start_detection should return a job id and the default status of a textract response
    # because it hasn't been updated yet.
    assert textract_result.job_id == "1234"
    assert textract_result.status == "NOT_STARTED"


def test_update_job_status_succeeded(
    textract_sopn_helper, get_document_analysis_json
):
    official_document = textract_sopn_helper.official_document
    AWSTextractParsedSOPN.objects.create(
        sopn=official_document,
        job_id="1234",
        raw_data="",
        status="NOT_STARTED",
    )

    with patch(
        "sopn_parsing.helpers.extract_pages.TextractSOPNHelper.textract_get_document_analysis"
    ) as mock_textract_get_document_analysis:
        mock_textract_get_document_analysis.return_value = (
            get_document_analysis_json
        )
        textract_sopn_helper.update_job_status()
    assert official_document.awstextractparsedsopn.status == "SUCCEEDED"


def test_update_job_status_failed(textract_sopn_helper, failed_analysis):
    official_document = textract_sopn_helper.official_document
    AWSTextractParsedSOPN.objects.create(
        sopn=official_document,
        job_id="1234",
        raw_data="",
        status="NOT_STARTED",
    )

    with patch(
        "sopn_parsing.helpers.extract_pages.TextractSOPNHelper.textract_get_document_analysis"
    ) as mock_textract_get_document_analysis:
        mock_textract_get_document_analysis.return_value = failed_analysis
        textract_sopn_helper.update_job_status()
    official_document.awstextractparsedsopn.refresh_from_db()
    assert official_document.awstextractparsedsopn.status == "FAILED"


def analysis_with_next_token_side_effect(job_id, next_token=None):
    if next_token == "token":
        return {"JobStatus": "SUCCEEDED", "Blocks": ["foo", "Bar"]}
    return {"JobStatus": "SUCCEEDED", "NextToken": "token", "Blocks": ["baz"]}


def test_update_job_status_with_token(textract_sopn_helper):
    official_document = textract_sopn_helper.official_document
    AWSTextractParsedSOPN.objects.create(
        sopn=official_document,
        job_id="1234",
        raw_data="",
        status="NOT_STARTED",
    )

    with patch(
        "sopn_parsing.helpers.extract_pages.TextractSOPNHelper.textract_get_document_analysis",
        side_effect=analysis_with_next_token_side_effect,
    ) as mock_textract_get_document_analysis:
        mock_textract_get_document_analysis.return_value = Mock(
            side_effect=analysis_with_next_token_side_effect
        )
        textract_sopn_helper.update_job_status()
    assert official_document.awstextractparsedsopn.status == "SUCCEEDED"
    assert (
        official_document.awstextractparsedsopn.raw_data
        == '{"JobStatus": "SUCCEEDED", "Blocks": ["baz", "foo", "Bar"]}'
    )


@pytest.fixture
def textract_sopn_parsing_helper(db, get_document_analysis_json):
    official_document = OfficialDocument.objects.create(
        ballot=BallotPaperFactory(),
        document_type=OfficialDocument.NOMINATION_PAPER,
    )
    yield TextractSOPNParsingHelper(official_document=official_document)
