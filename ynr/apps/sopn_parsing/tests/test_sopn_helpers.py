import json
import os
from pathlib import Path
from unittest.mock import PropertyMock

import pytest
from candidates.tests.factories import (
    BallotPaperFactory,
)
from candidates.tests.uk_examples import UK2015ExamplesMixin
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from mock import Mock
from official_documents.models import BallotSOPN
from sopn_parsing.helpers.text_helpers import clean_text
from sopn_parsing.helpers.textract_helpers import (
    get_extractor_class,
)
from sopn_parsing.models import AWSTextractParsedSOPN
from textractor.entities.lazy_document import LazyDocument


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
