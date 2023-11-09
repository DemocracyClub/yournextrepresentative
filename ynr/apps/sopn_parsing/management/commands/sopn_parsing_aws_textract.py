import os
from time import sleep

import boto3
from django.core.management.base import BaseCommand
from official_documents.models import TextractResult

# this is an html saved as a pdf
# test_sopn = "https://www.bury.gov.uk/council-and-democracy/elections-and-voting/statement-of-persons-nominated/"
test_sopn = (
    "ynr/apps/sopn_parsing/management/commands/test_sopns/HackneySOPN.pdf"
)

accepted_file_types = [
    ".pdf",
    ".jpg",
    ".jpeg",
    ".png",
    ".tif",
    ".tiff",
]

s3 = boto3.client("s3")
textract_client = boto3.client("textract")
session = boto3.session.Session(
    aws_access_key_id=os.environ.get("AWS_ACCESS_KEY_ID"),
    aws_secret_access_key=os.environ.get("AWS_SECRET_ACCESS_KEY"),
    aws_session_token=os.environ.get("AWS_SECURITY_TOKEN"),
)


class Command(BaseCommand):
    def handle(self, *args, **options):
        self.start_detection(test_sopn)

    def start_detection(self, test_sopn):
        """This is Step 1 of the SOPN parsing process using AWS Textract.
        https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/textract/client/get_document_analysis.html#
        """

        with open(test_sopn, "rb") as file:
            file_bytes = bytearray(file.read())
        region = "eu-west-2"
        bucket_name = "public-sopns"
        s3_client = boto3.client("s3", region_name=region)
        object_key = "test/test_sopn.pdf"

        response = s3_client.put_object(
            Bucket=bucket_name,
            Key=object_key,
            Body=file_bytes,
        )
        print(f"Uploaded bytes to s3://{bucket_name}/{object_key}")
        response = textract_client.start_document_analysis(
            DocumentLocation={
                "S3Object": {
                    "Bucket": bucket_name,
                    "Name": object_key,
                }
            },
            FeatureTypes=["TABLES", "FORMS"],
            OutputConfig={
                "S3Bucket": "public-sopns",
                "S3Prefix": "test",
            },
        )
        if response["JobId"]:
            job_id = response["JobId"]
            self.get_job_results(job_id)
        else:
            print("Job failed to start")
            raise Exception("Job failed to start")

    def get_job_results(self, job_id):
        """This is Step 2 of the SOPN parsing process using AWS Textract.
        https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/textract/client/get_document_analysis.html#
        """
        response = textract_client.get_document_analysis(JobId=job_id)
        ## this is a temp approach to step 2 to get the job id for dev env
        while response["JobStatus"] not in ["SUCCEEDED", "FAILED"]:
            sleep(5)
            response = textract_client.get_document_analysis(JobId=job_id)

        if response["JobStatus"] == "SUCCEEDED":
            # how do we ensure that the upload is unique if the
            # job id is unique with every upload? this won't likely
            # be an issue in production as we'll be uploading
            # files from the s3 bucket
            textract_result = TextractResult.objects.create(
                job_id=job_id,
                json_response=response,
            )
            textract_result.save()
            print(f"Job succeeded:{job_id}")
            print(
                "The number of pages in this document is:",
                response["DocumentMetadata"]["Pages"],
            )
            self.parse_aws_textract_response(response)
        elif response["JobStatus"] == "FAILED":
            print(f"Job failed:{job_id}")
            print(response["StatusMessage"])
        else:
            print(f"Job {job_id} still running")

    def parse_aws_textract_response(self, response):
        """This method takes a response from AWS Textract
        and parses the data into a table. The alternative
        to this aproach would be the use of SNS to send
        the response to a lambda function which would then
        parse the data into a table."""
        from trp import Document

        doc = Document(response)

        for page in doc.pages:
            for page in doc.pages:
                for table in page.tables:
                    for r, row in enumerate(table.rows):
                        for c, cell in enumerate(row.cells):
                            if "Candidate" in cell.text:
                                candidate_column = c
                            if "Description" in cell.text:
                                description_column = c
                                for r, row in enumerate(table.rows):
                                    for c, cell in enumerate(row.cells):
                                        if c == candidate_column:
                                            candidates = []
                                            candidates.append(cell.text)
                                        if c == description_column:
                                            descriptions = []
                                            descriptions.append(cell.text)
                                            for candidate, description in zip(
                                                candidates, descriptions
                                            ):
                                                print(
                                                    f"{candidate}: {description}"
                                                )
