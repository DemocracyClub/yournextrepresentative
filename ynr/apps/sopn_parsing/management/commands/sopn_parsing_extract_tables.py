from sopn_parsing.helpers.command_helpers import BaseSOPNParsingCommand
from sopn_parsing.helpers.extract_tables import extract_ballot_table
from sopn_parsing.helpers.text_helpers import NoTextInDocumentError


class Command(BaseSOPNParsingCommand):
    help = """
    Parse tables out of PDFs in to ParsedSOPN models for later parsing.
    """

    def handle(self, *args, **options):
        qs = self.get_queryset(options)
        filter_kwargs = {}
        if not options["ballot"] and not options["testing"]:
            if not options["reparse"]:
                filter_kwargs["officialdocument__parsedsopn"] = None

            qs = qs.filter(**filter_kwargs)

        # We can't extract tables when we don't know about the pages
        qs = qs.exclude(officialdocument__relevant_pages="")
        for ballot in qs:
            try:
                extract_ballot_table(ballot)
            except NoTextInDocumentError:
                self.stdout.write(
                    f"{ballot} raised a NoTextInDocumentError trying to extract tables"
                )
            except ValueError:
                self.stdout.write(
                    f"{ballot} raised a ValueError trying extract tables"
                )
