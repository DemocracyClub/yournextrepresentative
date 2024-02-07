from pdfminer.pdftypes import PDFException
from sopn_parsing.helpers.command_helpers import BaseSOPNParsingCommand
from sopn_parsing.helpers.extract_pages import extract_pages_for_ballot
from sopn_parsing.helpers.text_helpers import NoTextInDocumentError


class Command(BaseSOPNParsingCommand):
    help = """
    Parse documents to extract and set relevant pages from documents that have
    more than one ballot paper

    Default is to only parse documents for current electons that haven't
    already been parsed. Use `all-documents` and `reparse` to change this.

    """

    def handle(self, *args, **options):
        qs = self.get_queryset(options)
        qs = qs.distinct("officialdocument__source_url")
        filter_kwargs = {}
        if not options["ballot"] and not options["testing"]:
            if not options["reparse"]:
                filter_kwargs["officialdocument__relevant_pages"] = ""
            qs = qs.filter(**filter_kwargs)

        for ballot in qs:
            try:
                extract_pages_for_ballot(ballot)
            except (
                ValueError,
                NoTextInDocumentError,
                PDFException,
                FileNotFoundError,
            ) as e:
                try:
                    self.stderr.write(e.args[0])
                except AttributeError:
                    self.stderr.write(str(e))
