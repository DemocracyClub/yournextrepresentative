import json
from typing import Optional

import boto3
from botocore.client import Config
from django.conf import settings
from django.db import IntegrityError
from official_documents.models import OfficialDocument
from pdfminer.pdftypes import PDFException
from PIL import Image
from sopn_parsing.helpers.pdf_helpers import SOPNDocument
from sopn_parsing.helpers.text_helpers import NoTextInDocumentError
from sopn_parsing.models import (
    AWSTextractParsedSOPN,
    AWSTextractParsedSOPNImage,
)
from textractor import Textractor
from textractor.data.constants import TextractAPI, TextractFeatures
from textractor.entities.lazy_document import LazyDocument


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
        if len(sopn.pages) == 1 or sopn.matched_page_numbers == "all":
            textract_helper = TextractSOPNHelper(ballot.sopn)
            textract_helper.start_detection()

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


class NotUsingAWSException(ValueError):
    """
    Used to indicate that we're not in an environment that's not
    using AWS S3 storages
    """


class TextractSOPNHelper:
    """Get the AWS Textract results for a given SOPN."""

    def __init__(
        self,
        official_document: OfficialDocument,
        bucket_name: str = None,
        upload_path: str = None,
    ):
        self.official_document = official_document
        self.bucket_name = bucket_name or getattr(
            settings, "AWS_STORAGE_BUCKET_NAME", None
        )
        self.upload_path = upload_path
        if not any((self.bucket_name, self.upload_path)):
            raise NotUsingAWSException()
        self.extractor = Textractor(region_name="eu-west-2")

    def start_detection(self, replace=False) -> Optional[AWSTextractParsedSOPN]:
        parsed_sopn = getattr(
            self.official_document, "awstextractparsedsopn", None
        )
        if parsed_sopn and not replace:
            return None
        document = self.textract_start_document_analysis()
        try:
            textract_result, _ = AWSTextractParsedSOPN.objects.update_or_create(
                sopn=self.official_document,
                defaults={"raw_data": "", "job_id": document.job_id},
            )
            textract_result.save()
            textract_result.refresh_from_db()
            # Delete any old images that might exist for this SOPN
            textract_result.images.all().delete()
            for i, image in enumerate(document.images):
                AWSTextractParsedSOPNImage.objects.create(
                    image=AWSTextractParsedSOPNImage.pil_to_content_image(
                        image, f"page_{i}.png"
                    ),
                    parsed_sopn=textract_result,
                )
            return textract_result
        except IntegrityError as e:
            raise IntegrityError(
                f"Failed to create AWSTextractParsedSOPN for {self.official_document.ballot.ballot_paper_id}: error {e}"
            )

    def textract_start_document_analysis(self) -> LazyDocument:
        document: LazyDocument = self.extractor.start_document_analysis(
            file_source=f"s3://{self.bucket_name}{settings.MEDIA_URL}{self.official_document.uploaded_file.name}",
            features=[TextractFeatures.TABLES],
            s3_output_path=f"s3://{settings.TEXTRACT_S3_BUCKET_NAME}/raw_textract_responses",
            s3_upload_path=self.upload_path,
        )
        return document

    def update_job_status(self, blocking=False, reparse=False):
        COMPLETED_STATES = ("SUCCEEDED", "FAILED", "PARTIAL_SUCCESS")
        textract_result = self.official_document.awstextractparsedsopn
        if textract_result.status in COMPLETED_STATES and not reparse:
            return textract_result

        if not blocking:
            # If we're not blocking, simply check the status and save it
            # In the case that it's not finished, just save the status and return
            response = self.extractor.textract_client.get_document_analysis(
                JobId=textract_result.job_id
            )
            textract_result.status = response["JobStatus"]
            if response["JobStatus"] not in COMPLETED_STATES:
                textract_result.save()
                return textract_result

        # extractor.get_result is blocking by default (e.g, it will poll
        # for the job finishing see
        # https://github.com/aws-samples/amazon-textract-textractor/issues/326)
        # because the above check for `if not blocking` should have returned
        # by now if we didn't want to block (or the job is finished)
        # it's safe to call this and have it 'block' on noting.
        textract_document = self.extractor.get_result(
            textract_result.job_id, TextractAPI.ANALYZE
        )
        # Add the images back in manually
        images = list(textract_result.images.all())
        for i, page in enumerate(textract_document._pages):
            page.image = Image.open(images[i].image)
        for i, page in enumerate(textract_document.pages):
            images[i].image = AWSTextractParsedSOPNImage.pil_to_content_image(
                page.visualize(), f"page_{i}_annotated.png"
            )
            images[i].save()

        textract_result.status = textract_document.response["JobStatus"]
        textract_result.raw_data = json.dumps(textract_document.response)
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
