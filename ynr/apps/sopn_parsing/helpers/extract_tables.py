import json

import camelot

from sopn_parsing.helpers.text_helpers import clean_text
from sopn_parsing.models import ParsedSOPN
from sopn_parsing.helpers.text_helpers import NoTextInDocumentError


def extract_ballot_table(ballot, parse_flavor="lattice"):
    """
    Given a OfficialDocument model, update or create a ParsedSOPN model with the
    contents of the table as a JSON string.

    :type ballot: candidates.models.Ballot

    """
    document = ballot.sopn
    if not document.relevant_pages:
        raise ValueError(
            "Pages for table not known for document, extract page numbers first"
        )

    try:
        tables = camelot.read_pdf(
            document.uploaded_file.url,
            pages=document.relevant_pages,
            flavor=parse_flavor,
        )
    except (NotImplementedError, AttributeError):
        # * NotImplementedError is thrown if the PDF is an image or generally
        #   unreadable.
        # * AttributeError is thrown on some PDFs saying they need a password.
        #   Assume this is a bug in camelot, and ignore these PDFs
        raise NoTextInDocumentError()

    # Tables can span pages, camelot assumes they're different tables, so we
    # need to join them back together
    table_list = []
    for table in tables:
        table_list.append(table)
    table_list.sort(key=lambda t: (t.page, t.order))

    if not table_list:
        return

    table_data = table_list.pop(0).df
    for table in table_list:
        # It's possible to have the "situation of poll" document on the SOPN
        # Ignore any table that contains "polling station" (SOPNs tables don't)
        first_row = table.df.iloc[0].to_string()
        if "polling station" in clean_text(first_row):
            break
        # Append the continuation table to the first one in the document.
        # ignore_index is needed so the e.g table 2 row 1 doesn't replace
        # table 1 row 1
        table_data = table_data.append(table.df, ignore_index=True)

    if not table_data.empty:
        parsed, _ = ParsedSOPN.objects.update_or_create(
            sopn=document,
            defaults={"raw_data": json.dumps(table_data.to_dict())},
        )
        return parsed
