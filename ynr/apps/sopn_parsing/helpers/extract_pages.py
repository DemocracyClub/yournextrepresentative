from sopn_parsing.helpers.pdf_helpers import SOPNDocument
from sopn_parsing.helpers.text_helpers import NoTextInDocumentError

from official_documents.models import OfficialDocument


def extract_pages_for_ballot(ballot):
    """
    Try to extract the page numbers for the latest SOPN document related to this
    ballot.

    Beacuse documents can apply to more than one ballot, we also perform
    "drive by" parsing of other ballots contained in a given document.

    :type ballot: candidates.models.PostExtraElection

    """

    sopn = ballot.sopn
    save_page_numbers_for_single_document(sopn)


def extract_pages_for_single_document(document):
    other_doc_models = OfficialDocument.objects.filter(
        source_url=document.source_url
    ).select_related("post_election", "post_election__post")

    filename = document.uploaded_file.path
    if not filename:
        return

    if other_doc_models.count() == 1:
        yield document, "all"
        return
    try:
        sopn = SOPNDocument(filename)
    except (NoTextInDocumentError):
        raise NoTextInDocumentError("No text in {}, skipping".format(filename))
    for other_doc in other_doc_models:
        pages = sopn.get_pages_by_ward_name(other_doc.post_election.post.label)
        if not pages:
            continue
        page_numbers = ",".join(str(p.page_number) for p in pages)
        yield other_doc, page_numbers


def save_page_numbers_for_single_document(document):
    for other_doc, pages in extract_pages_for_single_document(document):
        other_doc.relevant_pages = pages
        other_doc.save()
