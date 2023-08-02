from bulk_adding.models import RawPeople
from sopn_parsing.helpers.command_helpers import BaseSOPNParsingCommand
from sopn_parsing.helpers.parse_tables import parse_raw_data_for_ballot


class Command(BaseSOPNParsingCommand):
    help = """
    Convert the raw extracted tables on the ParsedSOPN model to a parsed
    RawPeople model, and set the status as parsed.

    """

    def build_filter_kwargs(self, options):
        """
        Build kwargs used to filter the BallotQuerySet that is parsed
        - Always skip any ballots where we do not have a ParsedSOPN to try to
        extract candidates from
        - When test flag is used, dont make any changes
        - When parsing a single ballot, dont make any changes
        - When reparsing, only use ballots where we have previously created a
          RawPeople object from a ParsedSOPN
        - Otherwise filter by unparsed ParsedSOPN objects
        """
        # Always skip any ballots where we do not have a ParsedSOPN to try to
        # extract candidates from
        filter_kwargs = {"officialdocument__parsedsopn__isnull": False}
        if options.get("testing"):
            return filter_kwargs

        if options.get("ballot"):
            return filter_kwargs

        if options.get("reparse"):
            filter_kwargs[
                "rawpeople__source_type"
            ] = RawPeople.SOURCE_PARSED_PDF
            return filter_kwargs

        filter_kwargs["officialdocument__parsedsopn__parsed_data"] = None

        # Where the status is unparsed
        filter_kwargs["officialdocument__parsedsopn__status"] = "unparsed"

        return filter_kwargs

    def handle(self, *args, **options):
        # filters that we never change with args. These two would raise
        # ValueErrors in the parse_raw_data_for_ballot function
        base_qs = self.get_queryset(options)

        filter_kwargs = self.build_filter_kwargs(options)

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
