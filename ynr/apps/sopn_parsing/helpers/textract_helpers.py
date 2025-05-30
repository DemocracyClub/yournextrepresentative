import json
from typing import Optional

import boto3
from botocore.config import Config
from django.conf import settings
from django.db import IntegrityError
from official_documents.models import BallotSOPN
from PIL import Image
from sopn_parsing.models import (
    AWSTextractParsedSOPN,
    AWSTextractParsedSOPNImage,
)
from textractor import Textractor
from textractor.data.constants import TextractAPI, TextractFeatures
from textractor.entities.lazy_document import LazyDocument

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
        ballot_sopn: BallotSOPN,
        bucket_name: str = None,
        upload_path: str = None,
    ):
        self.ballot_sopn = ballot_sopn
        self.bucket_name = bucket_name or getattr(
            settings, "AWS_STORAGE_BUCKET_NAME", None
        )
        self.upload_path = upload_path
        if not any((self.bucket_name, self.upload_path)):
            raise NotUsingAWSException()

        self.extractor = Textractor(region_name="eu-west-2")

    def start_detection(self, replace=False) -> Optional[AWSTextractParsedSOPN]:
        parsed_sopn = getattr(self.ballot_sopn, "awstextractparsedsopn", None)
        if parsed_sopn and not replace:
            return None
        print("Starting analysis")
        document = self.textract_start_document_analysis()
        print("Saving results")
        try:
            textract_result, _ = AWSTextractParsedSOPN.objects.update_or_create(
                sopn=self.ballot_sopn,
                defaults={"raw_data": "", "job_id": document.job_id},
            )
            textract_result.save()
            textract_result.refresh_from_db()
            # Delete any old images that might exist for this SOPN
            textract_result.images.all().delete()

            return textract_result
        except IntegrityError as e:
            raise IntegrityError(
                f"Failed to create AWSTextractParsedSOPN for {self.ballot_sopn.ballot.ballot_paper_id}: error {e}"
            )

    def textract_start_document_analysis(self) -> LazyDocument:
        document: LazyDocument = self.extractor.start_document_analysis(
            file_source=f"s3://{self.bucket_name}{settings.MEDIA_URL}{self.ballot_sopn.uploaded_file.name}",
            features=[TextractFeatures.TABLES],
            s3_output_path=f"s3://{settings.TEXTRACT_S3_BUCKET_NAME}/raw_textract_responses",
            s3_upload_path=self.upload_path,
            save_image=False,
        )
        return document

    def update_job_status(self, blocking=False, reparse=False):
        COMPLETED_STATES = ("SUCCEEDED", "FAILED", "PARTIAL_SUCCESS")
        textract_result = self.ballot_sopn.awstextractparsedsopn
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
        try:
            textract_document = self.extractor.get_result(
                textract_result.job_id, TextractAPI.ANALYZE
            )
        except Exception as e:
            print(
                f"Failed to get results for {self.ballot_sopn.ballot.ballot_paper_id}"
            )
            print(e)
            textract_result.status = "FAILED"
            textract_result.save()
            return None

        print("Saving images")
        textract_result.images.all().delete()
        images = self.extractor._get_document_images_from_path(
            f"s3://{self.bucket_name}{settings.MEDIA_URL}{self.ballot_sopn.uploaded_file.name}"
        )
        for i, image in enumerate(images):
            image_model = AWSTextractParsedSOPNImage.objects.create(
                parsed_sopn=textract_result,
            )
            image_model.image = AWSTextractParsedSOPNImage.pil_to_content_image(
                image, f"page_{i}.png"
            )
            image_model.save()
        print(
            f"Finished saving images for {self.ballot_sopn.ballot.ballot_paper_id}"
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

    def __init__(self, ballot_sopn: BallotSOPN):
        self.ballot_sopn = ballot_sopn
        self.parsed_sopn = self.ballot_sopn.awstextractparsedsopn

    def parse(self):
        self.parsed_sopn.parse_raw_data()
        self.parsed_sopn.save()
        return self.parsed_sopn
