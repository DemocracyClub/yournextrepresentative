from celery import shared_task

from candidates.models import Ballot

from sopn_parsing.helpers.extract_pages import extract_pages_for_ballot
from sopn_parsing.helpers.extract_tables import extract_ballot_table
from sopn_parsing.helpers.parse_tables import parse_raw_data_for_ballot


@shared_task
def extract_and_parse_tables_for_ballot(ballot_str):
    ballot = Ballot.objects.get(ballot_paper_id=ballot_str)
    extract_pages_for_ballot(ballot)
    extract_ballot_table(ballot)
    parse_raw_data_for_ballot(ballot)
