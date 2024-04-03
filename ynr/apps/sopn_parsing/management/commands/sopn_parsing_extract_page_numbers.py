from elections.models import Election
from official_documents.extract_pages import extract_pages_for_election_sopn
from pdfminer.pdftypes import PDFException
from sopn_parsing.helpers.command_helpers import BaseSOPNParsingCommand
from sopn_parsing.helpers.text_helpers import NoTextInDocumentError


class Command(BaseSOPNParsingCommand):
    help = """
    Parse documents to extract and set relevant pages from documents that have
    more than one ballot paper

    Default is to only parse documents for current electons that haven't
    already been parsed. Use `all-documents` and `reparse` to change this.

    """

    def handle(self, *args, **options):
        qs = Election.objects.all().exclude(electionsopn=None)

        filter_kwargs = {}
        if options.get("election_slugs"):
            filter_kwargs["slug__in"] = options.get("election_slugs").split(",")

        if options["current"]:
            filter_kwargs["current"] = True

        if options["date"]:
            filter_kwargs["election_date"] = options["date"]

        qs = qs.filter(**filter_kwargs)

        for election in qs:
            try:
                extract_pages_for_election_sopn(election.electionsopn)
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
