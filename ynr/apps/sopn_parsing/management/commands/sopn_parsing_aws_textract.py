from official_documents.models import OfficialDocument
from sopn_parsing.helpers.command_helpers import BaseSOPNParsingCommand
from sopn_parsing.helpers.extract_pages import (
    TextractSOPNHelper,
    TextractSOPNParsingHelper,
)


class Command(BaseSOPNParsingCommand):
    def add_arguments(self, parser):
        super().add_arguments(parser)
        parser.add_argument(
            "--blocking",
            action="store_true",
            help="Wait for AWS to parse each SOPN",
        )
        parser.add_argument(
            "--start-analysis",
            action="store_true",
            help="Start AWS Textract analysis for each SOPN",
        )
        parser.add_argument(
            "--get-results",
            action="store_true",
            help="Get AWS Textract results for each SOPN",
        )

    def handle(self, *args, **options):
        queryset = self.get_queryset(options)
        if options["start_analysis"]:
            for ballot in queryset:
                official_documents = OfficialDocument.objects.filter(
                    ballot=ballot
                )
                official_document = official_documents.last()
                textract_helper = TextractSOPNHelper(official_document)
                # TO DO: add logging here
                textract_helper.start_detection(official_document)
        if options["get_results"]:
            for ballot in queryset:
                official_documents = OfficialDocument.objects.filter(
                    ballot=ballot
                )
                official_document = official_documents.last()
                textract_helper = TextractSOPNHelper(official_document)
                textract_result = textract_helper.update_job_status(
                    options["blocking"]
                )
                textract_sopn_parsing_helper = TextractSOPNParsingHelper(
                    official_document, textract_result=textract_result
                )
                textract_sopn_parsing_helper.create_df_from_textract_result(
                    official_document, textract_result=textract_result
                )
