from pdfminer.pdfparser import PDFSyntaxError
from official_documents.models import OfficialDocument
from sopn_parsing.helpers.pdf_helpers import SOPNDocument
from sopn_parsing.helpers.text_helpers import NoTextInDocumentError


def extract_pages_for_ballot(ballot, manual_upload=False):
    """
    Try to extract the page numbers for the latest SOPN document related to this
    ballot.

    Because documents can apply to more than one ballot, we also perform
    "drive by" parsing of other ballots contained in a given document.

    The manual_upload arg is used to force full page number extraction of from
    the document when it is uploaded manually, in case the document covers
    multiple ballots but this is the first ballot where it is being uploaded

    :type ballot: candidates.models.Ballot

    """
    # check if this is the only document with this source url and if so attempt
    # some optimisations before we try and parse the page numbers
    try:
        document = OfficialDocument.objects.get(
            source_url=ballot.sopn.source_url
        )
        # if this isn't a manual upload we assume all pages relate to the ballot
        # and can return early
        if not manual_upload:
            document.relevant_pages = "all"
            return document.save()
    except OfficialDocument.MultipleObjectsReturned:
        document = ballot.sopn

    # otherwise parse as if we had multiple sources as the SOPN may cover
    # multiple ballots, but this is the first time parsing it
    try:
        sopn = SOPNDocument(
            file=document.uploaded_file, source_url=document.source_url
        )
        return sopn.match_all_pages()
    except (NoTextInDocumentError):
        raise NoTextInDocumentError(
            f"Failed to extract pages for {document.uploaded_file.path} as a NoTextInDocumentError was raised"
        )
    except PDFSyntaxError:
        print(
            f"{ballot.ballot_paper_id} failed to parse as a PDFSyntaxError was raised"
        )
        raise PDFSyntaxError(
            f"Failed to extract pages for {document.uploaded_file.path} as a PDFSyntaxError was raised"
        )
