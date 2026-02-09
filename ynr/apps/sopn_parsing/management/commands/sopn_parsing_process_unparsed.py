from django.core.management.base import BaseCommand
from sopn_parsing.helpers.parse_tables import parse_raw_data_for_ballot
from sopn_parsing.helpers.textract_helpers import (
    NotUsingAWSException,
    TextractSOPNHelper,
)
from sopn_parsing.models import (
    AWSTextractParsedSOPN,
    AWSTextractParsedSOPNStatus,
)


class Command(BaseCommand):
    """
    When we call BallotSOPN.parse we only actually half process the BallotSOPN.

    This is because we want to be able to call `parse` as part of the request/response cycle
    without blocking users too much.

    This script picks up where `parse` left off. It manages two cases:

    # AWS Textract

    We should have made a `AWSTextractParsedSOPN` with `job_id` populated.
    Textract is async, so the initial `parse` just submits the data to AWS and
    gets a job_id.

    We need to check if the job ID has finished and pull in the data to `raw_data`.

    We need to parse the `raw_data` into `parsed_data` and makr a `RawData`
    object for bulk adding.
    """

    def handle(self, *args, **options):
        current_ballot_kwargs = {
            "sopn__ballot__election__current": True,
            "sopn__ballot__candidates_locked": False,
        }

        # Textract
        qs = AWSTextractParsedSOPN.objects.exclude(
            status__in=[
                AWSTextractParsedSOPNStatus.SUCCEEDED,
                AWSTextractParsedSOPNStatus.FAILED,
            ]
        ).filter(**current_ballot_kwargs)
        for aws_textract_model in qs:
            try:
                textract_helper = TextractSOPNHelper(aws_textract_model.sopn)
            except NotUsingAWSException:
                # Don't try to do anything more with Textract
                break
            # Get the status. If it's finished processing, this will set the raw_data
            # field (and do other things like make images)
            textract_helper.update_job_status()

        qs = (
            AWSTextractParsedSOPN.objects.filter(parsed_data=None)
            .exclude(raw_data="")
            .filter(**current_ballot_kwargs)
        )
        self.parse_tables_for_qs(qs)

    def parse_tables_for_qs(self, qs):
        for parsed_sopn_model in qs:
            try:
                parse_raw_data_for_ballot(parsed_sopn_model.sopn.ballot)
            except ValueError as e:
                print(str(e))
