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

    # if manual upload dont check for shared sources as this might be the first
    if not manual_upload and all_documents_with_source.count() == 1:
        yield document, "all"
        return
    try:
        sopn = SOPNDocument(doc_file)
    except (NoTextInDocumentError):
        raise NoTextInDocumentError(
            "No text in {}, skipping".format(document.uploaded_file.path)
        )
    for doc in all_documents_with_source:
        pages = sopn.get_pages_by_ward_name(doc.ballot.post.label)
        if not pages:
            continue
        page_numbers = ",".join(str(p.page_number) for p in pages)
        yield doc, page_numbers
