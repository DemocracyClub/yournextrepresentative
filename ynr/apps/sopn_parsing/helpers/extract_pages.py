import json
from time import sleep
from typing import Optional

import boto3
from botocore.client import Config
from django.conf import settings
from django.core.management import call_command
from django.db import IntegrityError
from official_documents.models import OfficialDocument
from pdfminer.pdftypes import PDFException
from sopn_parsing.helpers.pdf_helpers import SOPNDocument
from sopn_parsing.helpers.text_helpers import NoTextInDocumentError
from sopn_parsing.models import AWSTextractParsedSOPN


def extract_pages_for_ballot(ballot):
    """
    Try to extract the page numbers for the latest SOPN document related to this
    ballot.

    Because documents can apply to more than one ballot, we also perform
    "drive by" parsing of other ballots contained in a given document.

    :type ballot: candidates.models.Ballot

    """
    try:
        sopn = SOPNDocument(
            file=ballot.sopn.uploaded_file,
            source_url=ballot.sopn.source_url,
            election_date=ballot.election.election_date,
        )

        sopn.match_all_pages()
        if len(sopn.pages) == 1:
            call_command(
                "sopn_parsing_aws_textract",
                "--start-analysis",
                "--get-results",
                "--ballot",
                ballot.ballot_paper_id,
            )

    except NoTextInDocumentError:
        raise NoTextInDocumentError(
            f"Failed to extract pages for {ballot.sopn.uploaded_file.path} as a NoTextInDocumentError was raised"
        )
    except PDFException:
        print(
            f"{ballot.ballot_paper_id} failed to parse as a PDFSyntaxError was raised"
        )
        raise PDFException(
            f"Failed to extract pages for {ballot.sopn.uploaded_file.path} as a PDFSyntaxError was raised"
        )


config = Config(retries={"max_attempts": 5})

textract_client = boto3.client(
    "textract", region_name=settings.TEXTRACT_S3_BUCKET_REGION, config=config
)


class TextractSOPNHelper:
    """Get the AWS Textract results for a given SOPN."""

    def __init__(
        self,
        official_document: OfficialDocument,
        bucket_name: str = None,
    ):
        self.official_document = official_document

        self.bucket_name = bucket_name or settings.AWS_STORAGE_BUCKET_NAME

    def start_detection(self, replace=False) -> Optional[AWSTextractParsedSOPN]:
        parsed_sopn = getattr(
            self.official_document, "awstextractparsedsopn", None
        )
        if parsed_sopn and not replace:
            return None
        response = self.textract_start_document_analysis()
        try:
            textract_result, _ = AWSTextractParsedSOPN.objects.update_or_create(
                sopn=self.official_document,
                defaults={"raw_data": "", "job_id": response["JobId"]},
            )
            return textract_result
        except IntegrityError as e:
            raise IntegrityError(
                f"Failed to create AWSTextractParsedSOPN for {self.official_document.ballot.ballot_paper_id}: error {e}"
            )

    def textract_start_document_analysis(self):
        return textract_client.start_document_analysis(
            DocumentLocation={
                "S3Object": {
                    "Bucket": self.bucket_name,
                    "Name": f"{settings.MEDIA_URL}/{self.official_document.uploaded_file.name}".lstrip(
                        "/"
                    ),
                }
            },
            FeatureTypes=["TABLES", "FORMS"],
            OutputConfig={
                "S3Bucket": settings.TEXTRACT_S3_BUCKET_NAME,
                "S3Prefix": "raw_textract_responses",
            },
        )

    def textract_get_document_analysis(self, job_id, next_token=None):
        if next_token:
            return textract_client.get_document_analysis(
                JobId=job_id, NextToken=next_token
            )
        return textract_client.get_document_analysis(JobId=job_id)

    def update_job_status(self, blocking=False, reparse=False):
        COMPLETED_STATES = ("SUCCEEDED", "FAILED", "PARTIAL_SUCCESS")
        status = self.official_document.awstextractparsedsopn.status
        if status in COMPLETED_STATES and not reparse:
            # TODO: should we delete the instance of the textract result?
            return None
        textract_result = self.official_document.awstextractparsedsopn
        job_id = textract_result.job_id

        response = self.textract_get_document_analysis(job_id)
        textract_result.status = response["JobStatus"]

        if blocking:
            while response["JobStatus"] not in [
                "SUCCEEDED",
                "FAILED",
                "PARTIAL_SUCCESS",
            ]:
                sleep(5)
                response = self.textract_get_document_analysis(job_id)

        if response["JobStatus"] == "SUCCEEDED":
            # It's possible that the returned result will be truncated.
            # In this case you need to use the next token to get
            # subsequent parts of the response.
            blocks = []
            while True:
                for block in response["Blocks"]:
                    blocks.append(block)
                if "NextToken" not in response:
                    break
                response = self.textract_get_document_analysis(
                    job_id, next_token=response["NextToken"]
                )
            response["Blocks"] = blocks

        textract_result.raw_data = json.dumps(response)
        textract_result.save()
        return textract_result


class TextractSOPNParsingHelper:
    """Helper class to extract the AWS Textract blocks for a given SOPN
    and return the results as a dataframe. This is not to be confused with
    the SOPN parsing functionality that matches fields including
    candidates to parties."""

    def __init__(self, official_document: OfficialDocument):
        self.official_document = official_document
        self.parsed_sopn = self.official_document.awstextractparsedsopn

    def parse(self):
        self.parsed_sopn.parse_raw_data()
        self.parsed_sopn.save()
        return self.parsed_sopn
