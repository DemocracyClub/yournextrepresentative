from datetime import timedelta
from time import sleep

from django.conf import settings
from django.utils import timezone
from official_documents.models import BallotSOPN
from sopn_parsing.helpers.command_helpers import BaseSOPNParsingCommand
from sopn_parsing.helpers.textract_helpers import (
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
        parser.add_argument(
            "--upload-path",
            action="store",
            help="For texting only: the S3 bucket path to upload local SOPNs to, in the form of s3://[bucket]/[prefix]/",
        )
        parser.add_argument(
            "--reparse",
            action="store",
            help="Don't ignore BallotSOPNs that already have been parsed",
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
            sopn__awstextractparsedsopn__status__in=[
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
                qs = qs.exclude(sopn__awstextractparsedsopn__id=None)
            for ballot in qs:
                self.stdout.write(
                    f"Starting analysis for {ballot.ballot_paper_id}"
                )
                ballot_sopn: BallotSOPN = ballot.sopn
                if self.queue_full():
                    self.stdout.write(
                        f"Queue full, sleeping {settings.TEXTRACT_BACKOFF_TIME}"
                    )
                    self.check_all_documents(options)
                    sleep(settings.TEXTRACT_BACKOFF_TIME)
                textract_helper = TextractSOPNHelper(
                    ballot_sopn, upload_path=options["upload_path"]
                )
                # TO DO: add logging here
                if getattr(ballot_sopn, "textract_result", None):
                    continue
                sleep(settings.TEXTRACT_STAT_JOBS_PER_SECOND_QUOTA)
                textract_helper.start_detection(ballot_sopn)
        if options["get_results"]:
            qs = qs.filter(sopn__awstextractparsedsopn__isnull=False)
            if not options["reparse"]:
                qs = qs.filter(sopn__awstextractparsedsopn__parsed_data=None)
            for ballot in qs:
                print(ballot)
                ballot_sopn: BallotSOPN = ballot.sopn
                print(ballot_sopn)

                textract_helper = TextractSOPNHelper(ballot_sopn)
                textract_helper.update_job_status(
                    blocking=options["blocking"], reparse=options["reparse"]
                )

                textract_sopn_parsing_helper = TextractSOPNParsingHelper(
                    ballot_sopn
                )
                parsed = textract_sopn_parsing_helper.parse()
                print(parsed.as_pandas)
        self.check_all_documents(options)
