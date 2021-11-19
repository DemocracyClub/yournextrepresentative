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
    for other_doc, pages in extract_pages_for_single_document(
        document=ballot.sopn, manual_upload=manual_upload
    ):
        other_doc.relevant_pages = pages
        other_doc.save()


def extract_pages_for_single_document(document, manual_upload):

    # check if this is the only document with this source url and if so attempt
    # some optimisations before we try and parse the page numbers
    try:
        OfficialDocument.objects.get(source_url=document.source_url)
    except OfficialDocument.MultipleObjectsReturned:
        pass
    else:
        # if this isn't a manual upload we assume all pages relate to the ballot
        if not manual_upload:
            return [(document, "all")]

        # if the document is for a by-election, make the same assumption
        # NB there are edge cases where this is not always the case
        if ".by." in document.ballot.ballot_paper_id:
            return [(document, "all")]

    # otherwise parse as if we had multiple sources as the SOPN may cover
    # multiple ballots, but this is the first time parsing it
    try:
        sopn = SOPNDocument(
            file=document.uploaded_file, source_url=document.source_url
        )
        return sopn.match_all_pages()
    except (NoTextInDocumentError):
        raise NoTextInDocumentError(
            "No text in {}, skipping".format(document.uploaded_file.path)
        )
