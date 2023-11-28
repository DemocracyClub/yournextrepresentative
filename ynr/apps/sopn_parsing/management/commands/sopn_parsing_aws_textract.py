import os
from io import StringIO
from time import sleep

import boto3
from django.core.management.base import BaseCommand
from official_documents.models import OfficialDocument, TextractResult
from sopn_parsing.models import AWSTextractParsedSOPN

# # this is a single page pdf SoPN for testing
# test_sopn = (
#     "ynr/apps/sopn_parsing/management/commands/test_sopns/HackneySOPN.pdf"
# )

# # this is a multipage page html saved as pdf SoPN for testing
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
official_document = OfficialDocument.objects.get(id=1)


class Command(BaseCommand):
    def handle(self, *args, **options):
        self.start_detection(test_sopn)

        if options["start_analysis"]:
            for official_document in queryset:
                textract_helper = TextractSOPNHelper(official_document)
                # TO DO: add logging here
                textract_helper.start_detection(official_document)
        if options["get_results"]:
            for official_document in queryset:
                textract_helper = TextractSOPNHelper(official_document)
                textract_helper.update_job_status(options["blocking"])
