from django.db.models.functions import Length
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
    all_documents_with_source = (
        OfficialDocument.objects.filter(source_url=document.source_url)
        .select_related("ballot", "ballot__post")
        .order_by(-Length("ballot__post__label"))
    )
    doc_file = document.uploaded_file
    if not doc_file:
        return

    # if there are multiple documents with the same source it suggests multi
    # page SOPN covering multiple ballots
    if all_documents_with_source.count() == 1:

        # if not a manual upload assume all pages relate to the ballot
        if not manual_upload:
            yield document, "all"
            return

        #  check if the ballot is for a by-election - if so it is very likely to
        # be for a single ballot
        ballot = all_documents_with_source.get().ballot
        if ".by." in ballot.ballot_paper_id:
            yield document, "all"
            return

    # ... otherwise parse is as if we had multiple sources as the document
    # may contain multiple ballots, but this is the first time parsing it

    try:
        sopn = SOPNDocument(doc_file, all_documents_with_source)
    except (NoTextInDocumentError):
        raise NoTextInDocumentError(
            "No text in {}, skipping".format(document.uploaded_file.path)
        )

    for doc, page_numbers in sopn.match_all_page():
        yield doc, page_numbers

    # for doc in all_documents_with_source:
    #     ward = doc.ballot.post.label
    #     pages = sopn.get_pages_by_ward_name(ward)
    #     if not pages:
    #         continue
    #     page_numbers = ",".join(str(p.page_number) for p in pages)
    #     yield doc, page_numbers
