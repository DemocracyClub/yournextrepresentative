import io
from io import StringIO
from typing import Dict, List, Optional

from candidates.models import Ballot
from django.core.files.base import ContentFile
from django.db import transaction
from django.db.models.functions import Length
from official_documents.models import (
    ElectionSOPN,
    PageMatchingMethods,
    add_ballot_sopn,
)
from pdfminer.converter import TextConverter
from pdfminer.layout import LAParams
from pdfminer.pdfdocument import PDFEncryptionError, PDFTextExtractionNotAllowed
from pdfminer.pdfinterp import PDFPageInterpreter, PDFResourceManager
from pdfminer.pdfpage import PDFPage
from pdfminer.pdfparser import PDFSyntaxError
from pdfminer.pdftypes import PDFException
from PyPDF2 import PdfReader, PdfWriter
from PyPDF2.errors import DependencyError, PdfReadError
from sopn_parsing.helpers.text_helpers import (
    MatchedPagesError,
    NoTextInDocumentError,
    clean_page_text,
    clean_text,
)


def extract_pages_for_election_sopn(election_sopn: ElectionSOPN):
    """
    Try to extract the page numbers for an ElectionSOPN

    """
    try:
        election_sopn_document = ElectionSOPNDocument(election_sopn)

        election_sopn_document.match_all_pages()
        if (
            len(election_sopn_document.pages) == 1
            or election_sopn_document.matched_page_numbers == "all"
        ):
            raise NotImplementedError(
                "TODO: Convert this to a BallotSOPN model, not an ElectionSOPN model"
            )

    except NoTextInDocumentError:
        # TODO: Flag that this ElectionSOPN needs manual matching, on the model
        raise NoTextInDocumentError(
            f"Failed to extract pages for {election_sopn.uploaded_file.path} as a NoTextInDocumentError was raised"
        )
    except PDFException:
        print(
            f"{election_sopn.election.slug} failed to parse as a PDFSyntaxError was raised"
        )
        raise PDFException(
            f"Failed to extract pages for {election_sopn.uploaded_file.path} as a PDFSyntaxError was raised"
        )


HEADING_SIZE = 0.3
CONTINUATION_THRESHOLD = 0.5


class SOPNPageText:
    """
    Represents a single page of text contained in a PDF.
    """

    def __init__(self, page_number, text):
        self.page_number = page_number
        self.raw_text = text
        self.text = clean_page_text(text)
        self.matched = None
        self.post_label_to_match = None
        self.previous_page = None

    def get_page_heading_set(self):
        """
        Split the page heading (as defined by `get_page_heading`) on space
        and convert that list in to a set (that is, de-duplicate strings).

        This is used to compare to other sets with set.intersection.
        """
        return set(self.get_page_heading().split(" "))

    def get_page_heading(self):
        """
        Get the top of each page, as defined by `HEADING_SIZE`.

        Do some basic cleaning of the heading.
        """
        words = clean_page_text(self.text).split(" ")
        threshold = int(len(words) * HEADING_SIZE)
        return " ".join(words[0:threshold])

    def contains_post_label(self, post_label=None):
        ward_name = post_label or self.post_label_to_match
        search_text = self.get_page_heading()
        wards = ward_name.split("/")
        return any(ward in search_text for ward in wards)

    @property
    def is_page_heading_very_different_to_document_heading(self):
        """
        Compares this page's heading with the heading for the document to check
        if they are very different from each other.
        This is done by taking the intersection of the two sets. If the length
        of the intersection set divided by the length of the documents heading
        set is less than CONTINUATION_THRESHOLD then we assume this is a
        "continuation" page and return True.
        If the divided number is greater than the CONTINUATION_THRESHOLD then we
        assume this is a top page and return False.
        """
        words_in_both_headers = self.document_heading_set.intersection(
            self.get_page_heading_set()
        )
        difference = len(words_in_both_headers) / len(self.document_heading_set)
        return difference < CONTINUATION_THRESHOLD

    def split_heading_on_ward_name(self, heading):
        """
        Takes some heading text, and splits it on the post label we are
        matching against
        """
        return " ".join(heading.partition(self.post_label_to_match)[0:2])

    @property
    def is_heading_indentical_to_previous_page_heading(self):
        """
        Check if the heading of the previous page and this page are indentical
        """
        previous_page_heading_up_to_ward_name = self.split_heading_on_ward_name(
            heading=self.previous_page.get_page_heading()
        )
        page_heading_up_to_ward_name = self.split_heading_on_ward_name(
            heading=self.get_page_heading()
        )
        return (
            page_heading_up_to_ward_name
            == previous_page_heading_up_to_ward_name
        )

    @property
    def is_continuation_page(self):
        """
        Take a set containing the document heading (returned from
        `get_page_heading_set`) and compare it to another heading set.
        If the headings up to the post label are identical, we assume the page
        is a continuation.
        """
        if self.previous_page is None:
            return False

        if self.is_page_heading_very_different_to_document_heading:
            return True

        # if the page heading is identical to last page assume it is a
        # continuation page
        return self.is_heading_indentical_to_previous_page_heading


class PDFProcessingError(ValueError):
    """
    A generic exception to raise when various other PDF parsing exceptions are raised.

    """


class ElectionSOPNDocument:
    """
    A wrapper around an ElectionSOPN that adds methods for matching and splitting up
    pages. Each split page can in turn be converted into a BallotSOPN.

    """

    def __init__(self, election_sopn: ElectionSOPN, strict=True):
        self.election_sopn = election_sopn
        try:
            self.pages = self.parse_pages()
        except (
            PDFSyntaxError,
            PDFTextExtractionNotAllowed,
            DependencyError,
            PDFEncryptionError,
        ) as exception:
            raise PDFProcessingError(
                f"Error processing {self.election_sopn.uploaded_file.url}: {exception}"
            )

        self.spliter_data = {}
        self.matched_pages = []
        self.strict = strict

    @property
    def document_heading_set(self):
        """
        Takes the heading from the first page in the document and returns it as
        a set
        """
        return self.pages[1].get_page_heading_set()

    @property
    def blank_doc(self):
        """
        Takes the heading from the first or second page (if any) in the document and checks if empty
        """
        if len(self.document_heading_set) >= 10:
            return False

        return (
            len(self.pages) > 1
            and len(self.pages[2].get_page_heading_set()) < 10
        )

    @property
    def matched_page_numbers(self) -> List[int]:
        """
        Returns a list containing the page numbers of matched pages
        """
        return [page.page_number for page in self.matched_pages]

    @property
    def unmatched_pages(self) -> List[SOPNPageText]:
        """
        Returns a list of pages not marked as matched
        """
        return [page for page in self.pages.values() if not page.matched]

    def is_matched_page_numbers_valid(self):
        """
        Validates that the matched page numbers are correct by checking they
        are sequential
        """
        # if we couldn't match any pages we still return True so that the
        # document is saved and can be checked in full manually
        if not self.matched_page_numbers:
            return True

        if len(self.matched_page_numbers) == 1:
            return True

        lower = min(self.matched_page_numbers)
        upper = max(self.matched_page_numbers) + 1
        return self.matched_page_numbers == list(range(lower, upper))

    def add_to_matched_pages(self, page):
        """
        Mark the page as matched, add it to the list of matched pages, and set
        this page as the previous page
        """
        page.matched = True
        self.matched_pages.append(page)

    def clear_old_matched_pages(self):
        """
        Remove any previously set matched pages and previous page attributes
        """
        self.matched_pages = []

    def match_ballot_to_pages(self, ballot: Ballot) -> Optional[List[int]]:
        """
        Given a ward name, loop over all the unmatched pages looking for the
        first match.

        Return a string in the format of:
           "1,2,3,4"

        For more on this format, see https://camelot-py.readthedocs.io/en/master/user/quickstart.html?highlight=pages#specify-page-numbers
        """
        matched_to_ballot = []
        for page in self.unmatched_pages:
            page.previous_page = self.pages.get(page.page_number - 1)
            page.document_heading_set = self.document_heading_set
            page.post_label_to_match = clean_text(ballot.post.label)

            if matched_to_ballot and not page.is_continuation_page:
                break

            # no matched pages, but we know this is a continuation page so don't
            # search for the post label in case of edge case such as the ward
            # name appears in a candidates address
            if matched_to_ballot and page.is_continuation_page:
                matched_to_ballot.append(page)
                continue

            if page.contains_post_label():
                matched_to_ballot.append(page)

        if not self.is_matched_page_numbers_valid():
            matched_page_str = ",".join(
                str(number) for number in self.matched_page_numbers
            )
            if self.strict:
                raise MatchedPagesError(
                    f"Page numbers are not consecutive for {self.election_sopn.source_url}. Pages: {matched_page_str}. Post: {ballot.post.label}"
                )
            print(
                f"Page numbers are not consecutive for {self.election_sopn.source_url}. Pages: {matched_page_str}. Post: {ballot.post.label}. Skipping."
            )
            return ""

        matched_page_numbers = []
        for page in matched_to_ballot:
            matched_page_numbers.append(page.page_number - 1)
            page.matched = True
        return matched_page_numbers

    def match_all_pages(self) -> None:
        for ballot in self.election_sopn.election.ballot_set.all().order_by(
            -Length("post__label"), "post__label"
        ):
            matched_pages = self.match_ballot_to_pages(ballot)
            self.spliter_data[ballot.ballot_paper_id] = matched_pages

        splitter = ElectionSOPNPageSplitter(
            self.election_sopn, self.spliter_data
        )
        splitter.split()

    def parse_pages(self) -> Dict[int, SOPNPageText]:
        """
        Returns a dictionary where the key is the page number, and the value is
        a SOPNPageText object
        """
        pages = {}
        rsrcmgr = PDFResourceManager()

        laparams = LAParams(line_margin=0.1)
        fp = self.election_sopn.uploaded_file.file

        for page_no, page in enumerate(
            PDFPage.get_pages(fp, check_extractable=True), start=1
        ):
            retstr = StringIO()
            device = TextConverter(rsrcmgr, retstr, laparams=laparams)
            interpreter = PDFPageInterpreter(rsrcmgr, device)
            interpreter.process_page(page)
            pages[page_no] = SOPNPageText(page_no, retstr.getvalue())
            device.close()
            retstr.close()
        fp.close()
        return pages


def clean_matcher_data(ballot_to_pages):
    """
    For simplicity, Svelte only POSTs the data of exact pages that
    have been matched to a ballot.

    We want to deal with a couple of things here:

    1. Continuation page: we need to fill in the gaps of pages that have not been matched
    2. Out of order pages: it's not always true that the pages in the SOPN are in order.

    :return:
    """
    # It's not valid to have no matched all page
    if not all(ballot_data["matched_page"] for ballot_data in ballot_to_pages):
        raise ValueError("Not all ballots matched")

    # First, convert the matched_page to a list of pages
    for ballot_data in ballot_to_pages:
        if matched_page := ballot_data.pop("matched_page", None):
            ballot_data["matched_pages"] = [int(matched_page)]
        else:
            ballot_data["matched_pages"] = []

    cleaned_data = {
        ballot_data["ballot_paper_id"]: ballot_data["matched_pages"]
        for ballot_data in ballot_to_pages
    }

    # Now, sort the list by the first matched page
    sorted_data = sorted(cleaned_data.items(), key=lambda x: x[1][0])

    for i in range(len(sorted_data) - 1):
        this_ballot, this_value = sorted_data[i]
        next_ballot, next_value = sorted_data[i + 1]

        if this_value[-1] + 1 < next_value[0]:
            this_value.extend(range(this_value[-1] + 1, next_value[0]))

    return cleaned_data


class ElectionSOPNPageSplitter:
    def __init__(
        self, election_sopn: ElectionSOPN, ballot_to_pages: Dict[str, List[int]]
    ):
        """
        ballot_to_pages MUST be 0th indexed, so the first page is page 0
        """
        self.election_sopn = election_sopn
        self.ballot_to_pages = ballot_to_pages
        if not self.election_sopn.uploaded_file.name.endswith("pdf"):
            raise PdfReadError("Not a PDF")
        self.reader = PdfReader(self.election_sopn.uploaded_file.open())

    @transaction.atomic()
    def split(
        self, method=PageMatchingMethods.AUTO_MATCHED, parse_ballots=True
    ):
        for ballot_paper_id, matched_pages in self.ballot_to_pages.items():
            pdf_pages = io.BytesIO()
            writer = PdfWriter()
            try:
                for page in matched_pages:
                    writer.add_page(self.reader.pages[page])
            except (PDFEncryptionError, DependencyError) as exception:
                raise PDFProcessingError(f"{exception}")

            writer.write(pdf_pages)
            pdf_pages.seek(0)
            pdf_content = ContentFile(
                pdf_pages.getvalue(),
                name=f"sopn-{ballot_paper_id}.pdf",
            )
            relevant_pages = ",".join([str(num) for num in matched_pages])
            if len(matched_pages) == len(self.reader.pages):
                relevant_pages = "all"
            if not relevant_pages:
                relevant_pages = "all"
            if len(relevant_pages) >= 20:
                # chances are this is an error, so raise
                raise PDFProcessingError(
                    f"Page matching error: {self.election_sopn.uploaded_file.url} matched to pages: {relevant_pages}"
                )

            ballot = Ballot.objects.get(ballot_paper_id=ballot_paper_id)

            add_ballot_sopn(
                ballot,
                pdf_content,
                self.election_sopn.source_url,
                relevant_pages,
                parse=parse_ballots,
            )

            self.election_sopn.page_matching_method = method
            self.election_sopn.save()
