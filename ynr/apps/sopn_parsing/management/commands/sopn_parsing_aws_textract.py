from datetime import timedelta
from time import sleep

from django.conf import settings
from django.utils import timezone
from official_documents.models import OfficialDocument
from sopn_parsing.helpers.command_helpers import BaseSOPNParsingCommand
from sopn_parsing.helpers.extract_pages import (
    TextractSOPNHelper,
    TextractSOPNParsingHelper,
)
from sopn_parsing.models import AWSTextractParsedSOPN


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
        processing = AWSTextractParsedSOPN.objects.filter(
            created__gt=time_window,
            status__in=["NOT_STARTED", "IN_PROGRESS"],
        )

        if count := processing.count() > settings.TEXTRACT_CONCURRENT_QUOTA:
            print(f"Processing: {count}")
            return True
        return False

    def get_queryset(self, options):
        return super().get_queryset(options)

    def check_all_documents(self, options, **kwargs):
        qs = self.get_queryset(options).filter(
            officialdocument__awstextractparsedsopn__status__in=[
                "NOT_STARTED",
                "IN_PROGRESS",
            ]
        )
        if qs:
            print(f"Checking {qs.count()} documents")
            for document in qs:
                textract_helper = TextractSOPNHelper(document.sopn)
                textract_helper.update_job_status(blocking=False)

    def handle(self, *args, **options):
        qs = self.get_queryset(options)
        # in start-analysis, we want the qs to be all documents
        # that don't have a textract result on the sopn
        # in get-results, we want the qs to be all documents
        # that have a textract result on the sopn
        # the following is repetitive but addresses both options
        if options["start_analysis"]:
            if not options["reparse"]:
                qs = qs.exclude(
                    officialdocument__awstextractparsedsopn__id=None
                )
            for ballot in qs:
                official_document: OfficialDocument = ballot.sopn
                if self.queue_full():
                    self.check_all_documents(options)
                    sleep(settings.TEXTRACT_BACKOFF_TIME)
                textract_helper = TextractSOPNHelper(official_document)
                # TO DO: add logging here
                if getattr(official_document, "textract_result", None):
                    continue
                sleep(settings.TEXTRACT_STAT_JOBS_PER_SECOND_QUOTA)
                textract_helper.start_detection(official_document)
        if options["get_results"]:
            qs = queryset.filter(
                officialdocument__textract_result__isnull=False
            )
            for ballot in qs:
                official_document: OfficialDocument = ballot.sopn

                textract_helper = TextractSOPNHelper(official_document)
                textract_helper.update_job_status(blocking=options["blocking"])

                textract_sopn_parsing_helper = TextractSOPNParsingHelper(
                    official_document
                )
                textract_sopn_parsing_helper.create_df_from_textract_result()
        self.check_all_documents(options)
