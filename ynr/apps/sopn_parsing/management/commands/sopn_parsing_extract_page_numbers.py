from django.core.management.base import BaseCommand

from official_documents.models import OfficialDocument
from sopn_parsing.helpers import SOPNDocument, NoTextInDocumentError


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

            other_doc_models = (
                OfficialDocument.objects.filter(source_url=document.source_url)
                .exclude(pk=document.pk)
                .select_related("post_election", "post_election__post")
            )

            try:
                for other_doc, pages in self.parse_single_document(
                    document, other_doc_models
                ):
                    other_doc.relevant_pages = pages
                    other_doc.save()
            except ValueError as e:
                self.stderr.write(e)
            seen_sources.add(document.source_url)

    def parse_single_document(self, document, other_doc_models):
        self.top_strings = []

        filename = document.uploaded_file.path
        if not filename:
            return

        if not other_doc_models.exists():
            yield document, "all"
            return
        try:
            sopn = SOPNDocument(filename)
        except (NoTextInDocumentError):
            self.stdout.write("No text in {}, skipping".format(filename))
            return
        for other_doc in other_doc_models:
            pages = sopn.get_pages_by_ward_name(
                other_doc.post_election.post.label
            )
            if not pages:
                raise ValueError(
                    "None of the ballots fund in file {}".format(filename)
                )
            page_numbers = ",".join(str(p.page_number) for p in pages)
            yield other_doc, page_numbers
