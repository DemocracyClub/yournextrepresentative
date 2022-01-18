import pypandoc
import tempfile
from pdfminer.pdfparser import PDFSyntaxError
from sopn_parsing.helpers.pdf_helpers import SOPNDocument
from sopn_parsing.helpers.text_helpers import NoTextInDocumentError
from official_documents.models import OfficialDocument


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
    if ballot.sopn.uploaded_file.path.endswith(".pdf"):
        pass
    elif ballot.sopn.uploaded_file.path.endswith(".html"):
        print(
            f"Warning! HTML file types are not supported; trying to convert {ballot.sopn.uploaded_file.path} to pdf"
        )

        html_file_path = ballot.sopn.uploaded_file.path

        with tempfile.NamedTemporaryFile(suffix=".pdf") as temp_file:
            # convert the doc and save to a temp file
            pypandoc.convert_file(
                html_file_path, to="pdf", outputfile=temp_file.name
            )

            # save the pdf file to the sopn document
            pdf_file_name = ballot.sopn.uploaded_file.name.split("/")[
                -1
            ].replace(".html", ".pdf")

            ballot.sopn.uploaded_file.save(
                name=pdf_file_name, content=temp_file, save=True
            )
            ballot.sopn.save()

    elif ballot.sopn.uploaded_file.path.endswith(".docx"):
        print(
            f"Warning! docx file types are not supported; trying to convert {ballot.sopn.uploaded_file.path} to pdf"
        )

        docx_file_path = ballot.sopn.uploaded_file.path

        with tempfile.NamedTemporaryFile(suffix=".pdf") as temp_file:
            pypandoc.convert_file(
                docx_file_path, to="pdf", outputfile=temp_file.name
            )

            pdf_file_name = ballot.sopn.uploaded_file.name.split("/")[
                -1
            ].replace(".docx", ".pdf")

            ballot.sopn.uploaded_file.save(
                name=pdf_file_name, content=temp_file, save=True
            )
            ballot.sopn.save()
    else:
        raise ValueError("File type not currently supported")
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
        print(
            "{ballot.ballot_paper_id}"
            + "Multiple documents with this source url"
        )
        document = ballot.sopn

    # otherwise parse as if we had multiple sources as the SOPN may cover
    # multiple ballots, but this is the first time parsing it
    try:
        sopn = SOPNDocument(
            file=ballot.sopn.uploaded_file, source_url=ballot.sopn.source_url
        )
        return sopn.match_all_pages()
    except (NoTextInDocumentError):
        raise NoTextInDocumentError(
            f"Failed to extract pages for {ballot.sopn.uploaded_file.path} as a NoTextInDocumentError was raised"
        )
    except PDFSyntaxError:
        print(
            f"{ballot.ballot_paper_id} failed to parse as a PDFSyntaxError was raised"
        )
        raise PDFSyntaxError(
            f"Failed to extract pages for {ballot.sopn.uploaded_file.path} as a PDFSyntaxError was raised"
        )
