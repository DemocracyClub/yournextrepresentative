from sopn_parsing.helpers.command_helpers import BaseSOPNParsingCommand
from sopn_parsing.helpers.extract_pages import (
    TextractSOPNHelper,
    TextractSOPNParsingHelper,
)


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
                textract_result = textract_helper.update_job_status(
                    options["blocking"]
                )
                textract_sopn_parsing_helper = TextractSOPNParsingHelper(
                    official_document, textract_result=textract_result
                )
                textract_sopn_parsing_helper.get_table_csv_results(
                    official_document, textract_result
                )
