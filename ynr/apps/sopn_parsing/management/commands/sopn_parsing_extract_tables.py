from sopn_parsing.helpers.extract_tables import extract_ballot_table
from sopn_parsing.helpers.text_helpers import NoTextInDocumentError
from sopn_parsing.helpers.command_helpers import BaseSOPNParsingCommand


class Command(BaseSOPNParsingCommand):
    help = """
    Parse tables out of PDFs in to ParsedSOPN models for later parsing.
    
    """

    def handle(self, *args, **options):
        qs = self.get_queryset(options)
        filter_kwargs = {}
        if not options["ballot"]:
            if not options["reparse"]:
                filter_kwargs["officialdocument__parsedsopn"] = None

            qs = qs.filter(**filter_kwargs)

        # We can't extract tables when we don't know about the pages
        qs = qs.exclude(officialdocument__relevant_pages=None)

        for ballot in qs:
            try:
                extract_ballot_table(ballot)
            except (ValueError, NoTextInDocumentError):
                self.stdout.write(
                    "Skipping {} due to parse error".format(ballot)
                )
