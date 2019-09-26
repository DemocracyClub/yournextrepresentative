from bulk_adding.models import RawPeople
from sopn_parsing.helpers.command_helpers import BaseSOPNParsingCommand
from sopn_parsing.helpers.parse_tables import parse_raw_data_for_ballot


class Command(BaseSOPNParsingCommand):
    help = """
    Convert the raw extracted tables on the ParsedSOPN model to a parsed 
    RawPeople model, and set the status as parsed.
    
    """

    def handle(self, *args, **options):
        filter_kwargs = {}
        if not options.get("ballot"):

            if options["reparse"]:
                # If reparsing, only reparse RawPeople created by parsing
                # from a PDF
                filter_kwargs["rawpeople"] = RawPeople.SOURCE_PARSED_PDF
            else:
                # Where no parsed data already exists
                filter_kwargs[
                    "officialdocument__parsedsopn__parsed_data"
                ] = None

                # Where the status is unparsed
                filter_kwargs[
                    "officialdocument__parsedsopn__status"
                ] = "unparsed"

        # filters that we never change with args. These two would raise
        # ValueErrors in the parse_raw_data_for_ballot function
        base_qs = self.get_queryset(options)

        qs = base_qs.filter(**filter_kwargs)
        qs = qs.filter(
            candidates_locked=False,  # Never parse a locked ballot
            suggestedpostlock=None,  # Never parse a ballot with lock suggestions
        )

        if not qs.exists():
            msg = ["No ballots to parse found."]

            if options.get("ballot"):
                msg.append(
                    "This ballot might be locked or have lock suggestions"
                )

            self.stderr.write("\n".join(msg))

        for ballot in qs:
            parse_raw_data_for_ballot(ballot)
