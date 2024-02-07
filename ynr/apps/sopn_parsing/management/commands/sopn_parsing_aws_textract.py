from datetime import timedelta
from time import sleep

from django.utils import timezone
from official_documents.models import OfficialDocument, TextractResult
from sopn_parsing.helpers.command_helpers import BaseSOPNParsingCommand
from sopn_parsing.helpers.extract_pages import (
    TextractSOPNHelper,
)

TEXTRACT_STAT_JOBS_PER_SECOND_QUOTA = 0.5  # TODO: move to settings
TEXTRACT_BACKOFF_TIME = 60
TEXTRACT_CONCURRENT_QUOTA = 80  # move to settings


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

    def queue_full(self):
        time_window = timezone.now() - timedelta(hours=1)
        processing = TextractResult.objects.filter(
            created__gt=time_window,
            analysis_status__in=["NOT_STARTED", "IN_PROGRESS"],
        )

        if count := processing.count() > TEXTRACT_CONCURRENT_QUOTA:
            print(f"Processing: {count}")
            return True
        return False

    def get_queryset(self, options):
        qs = super().get_queryset(options)
        return qs.filter(officialdocument__textract_result__id=None)

    def check_all_documents(self, options, **kwargs):
        qs = self.get_queryset(options).filter(
            officialdocument__textract_result__analysis_status__in=[
                "NOT_STARTED",
                "IN_PROGRESS",
            ]
        )
        if qs:
            print(f"Checking {qs.count()} documents")
            for document in qs:
                textract_helper = TextractSOPNHelper(document)
                textract_helper.update_job_status(blocking=False)

    def handle(self, *args, **options):
        queryset = self.get_queryset(options)

        for ballot in queryset:
            print(ballot)
            official_document: OfficialDocument = ballot.sopn
            if options["start_analysis"]:
                if self.queue_full():
                    self.check_all_documents(options)
                    sleep(TEXTRACT_BACKOFF_TIME)
                textract_helper = TextractSOPNHelper(official_document)
                # TO DO: add logging here
                if getattr(official_document, "textract_result", None):
                    continue
                sleep(TEXTRACT_STAT_JOBS_PER_SECOND_QUOTA)
                textract_helper.start_detection(official_document)
            if options["get_results"]:
                textract_helper = TextractSOPNHelper(official_document)
                textract_helper.update_job_status(blocking=options["blocking"])

                # Commented out for the time being
                # textract_sopn_parsing_helper = TextractSOPNParsingHelper(official_document)
                # textract_sopn_parsing_helper.create_df_from_textract_result()
        self.check_all_documents()
