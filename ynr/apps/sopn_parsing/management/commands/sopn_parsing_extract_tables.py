from django.core.management.base import BaseCommand

from official_documents.models import OfficialDocument
from sopn_parsing.helpers.extract_tables import extract_ballot_table
from sopn_parsing.helpers.text_helpers import NoTextInDocumentError


class Command(BaseCommand):
    help = """
    Parse tables out of PDFs in to ParsedSOPN models for later parsing.
    
    """

    def add_arguments(self, parser):
        parser.add_argument(
            "--ballot", action="store", help="Document(s) for a single ballot"
        )
        parser.add_argument(
            "--current",
            action="store_true",
            help="Only parse documents for current elections",
        )

    def handle(self, *args, **options):
        if options.get("ballot"):
            filter_kwargs = {
                "post_election__ballot_paper_id": options["ballot"]
            }
        else:
            filter_kwargs = {}
            if options.get("current"):
                filter_kwargs["post_election__election__current"] = True
            filter_kwargs["parsedsopn"] = None

        qs = OfficialDocument.objects.filter(**filter_kwargs).exclude(
            relevant_pages=None
        )

        for document in qs:
            try:
                extract_ballot_table(document)
            except (ValueError, NoTextInDocumentError):
                self.stdout.write(
                    "Skipping {} due to parse error".format(document)
                )
