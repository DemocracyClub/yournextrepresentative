from django.core.management.base import BaseCommand

from official_documents.models import OfficialDocument
from sopn_parsing.helpers.extract_pages import (
    save_page_numbers_for_single_document,
)
from sopn_parsing.helpers.text_helpers import NoTextInDocumentError


class Command(BaseCommand):
    help = """
    
    Parse documents to extract and set relevant pages from documents that have
    more than one ballot paper
    
    Default is to only parse documents for current electons that haven't 
    already been parsed. Use `all-documents` and `reparse` to change this.
    
    """

    def add_arguments(self, parser):
        parser.add_argument(
            "--all-documents",
            action="store_true",
            help="Parse document from all elections, not just current ones",
        )
        parser.add_argument(
            "--reparse",
            action="store_true",
            help="Reparse documents that have already been parsed",
        )

    def handle(self, *args, **options):

        filter_kwargs = {}

        if not options["reparse"]:
            filter_kwargs["relevant_pages"] = None

        if not options["all_documents"]:
            filter_kwargs["post_election__election__current"] = True

        qs = OfficialDocument.objects.filter(**filter_kwargs)
        seen_sources = set()
        for document in qs:
            if document.source_url in seen_sources:
                continue
            try:
                save_page_numbers_for_single_document(document)
            except (ValueError, NoTextInDocumentError) as e:
                self.stderr.write(e)
            seen_sources.add(document.source_url)
