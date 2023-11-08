import os
from time import sleep

import boto3
from django.core.management.base import BaseCommand
from official_documents.models import TextractResult

# this is an html saved as a pdf
# test_sopn = "https://www.bury.gov.uk/council-and-democracy/elections-and-voting/statement-of-persons-nominated/"
test_sopn = "ynr/apps/sopn_parsing/management/commands/test_sopns/BurySOPN.pdf"

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

        try:
            job_id = response["JobId"]
            self.get_job_results(job_id)
        except KeyError:
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
                "The number of result_pages in this document is:",
                {response["DocumentMetadata"]["Pages"]},
            )
            self.parse_pages(textract_result)
        elif response["JobStatus"] == "FAILED":
            print(f"Job failed:{job_id}")
            print(response["StatusMessage"])
        else:
            print(f"Job {job_id} still running")

    def parse_pages(self, textract_result):
        """This is Step 3 of the SOPN parsing process using AWS Textract."""
        results = textract_result.json_response
        pages = []
        # this step can be improved by using the BlockType to determine
        # what type of block we are dealing with and then parsing the
        # text accordingly
        for result_page in results["Blocks"]:
            if result_page["BlockType"] == "TABLE":
                print("I am a Table")
                print(result_page["Text"])
            if result_page["BlockType"] == "CELL":
                print("I am a Cell")
                print(result_page["Text"])
            if result_page["BlockType"] == "LINE":
                print("I am a Line")
                print(result_page["Text"])
            if result_page["BlockType"] == "WORD":
                print("I am a Word")
                print(result_page["Text"])
            if result_page["BlockType"] == "PAGE":
                print("I am a Page")
                pages.append(result_page)
