from django.db.models import OuterRef, Subquery
from official_documents.models import OfficialDocument
from sopn_parsing.helpers.command_helpers import BaseSOPNParsingCommand
from sopn_parsing.helpers.extract_tables import extract_ballot_table
from sopn_parsing.helpers.text_helpers import NoTextInDocumentError


class Command(BaseSOPNParsingCommand):
    help = """
    Parse tables out of PDFs in to CamelotParsedSOPN models for later parsing.
    """

    def handle(self, *args, **options):
        qs = self.get_queryset(options)
        filter_kwargs = {}
        if not options["ballot"] and not options["testing"]:
            if not options["reparse"]:
                filter_kwargs["officialdocument__camelotparsedsopn"] = None

            qs = qs.filter(**filter_kwargs)

        # We can't extract tables when we don't know about the pages
        # It is possible for an a ballot to have more than one
        # OfficialDocument so we need to get the latest one to check
        # that we know which pages to parse tables from
        latest_sopns = OfficialDocument.objects.filter(
            ballot=OuterRef("pk")
        ).order_by("-created")
        qs = qs.annotate(
            sopn_relevant_pages=Subquery(
                latest_sopns.values("relevant_pages")[:1]
            )
        )
        qs = qs.exclude(sopn_relevant_pages="")
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
