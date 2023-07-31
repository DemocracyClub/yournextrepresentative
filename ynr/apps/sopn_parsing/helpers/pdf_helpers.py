from io import StringIO
from typing import List

from django.db.models.functions import Length
from official_documents.models import OfficialDocument
from pdfminer.converter import TextConverter
from pdfminer.layout import LAParams
from pdfminer.pdfinterp import PDFPageInterpreter, PDFResourceManager
from pdfminer.pdfpage import PDFPage
from sopn_parsing.helpers.text_helpers import (
    MatchedPagesError,
    NoTextInDocumentError,
    clean_page_text,
    clean_text,
)

# Used by SOPNPageText.get_page_heading
HEADING_SIZE = 0.3

# Used by SOPNPageText.detect_top_page
CONTINUATION_THRESHOLD = 0.5


class SOPNDocument:
    def __init__(self, file, source_url, election_date, strict=False):
        """
        Represents a collection of pages from a single PDF file.
        """
        self.file = file
        self.source_url = source_url
        self.election_date = election_date
        self.strict = strict
        self.unmatched_documents = list(
            self.all_official_documents_with_source()
        )
        self.pages = self.parse_pages()
        self.matched_pages = []

        if self.blank_doc:
            raise NoTextInDocumentError

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
    def matched_page_numbers(self) -> List[str]:
        """
        Returns a list containing the page numbers of matched pages
        """
        return [page.page_number for page in self.matched_pages]

    @property
    def unmatched_pages(self):
        """
        Returns a list of pages not marked as matched
        """
        return [page for page in self.pages.values() if not page.matched]

    @property
    def guess_all_pages(self) -> bool:
        """
        Return if there is only one page or one related OfficialDocument
        """
        if len(self.pages) == 1:
            return True

        return len(self.pages) < 4 and len(self.unmatched_documents) == 1

    def all_official_documents_with_source(self):
        """
        Return a QuerySet of OfficialDocument objects that have the same
        source_url. These are ordered with the longest post label first as if
        the SOPN pdf contains wards with similar ward names, we want to try to
        match as specifically as possible first e.g. searching for "Foo North
        Ward" but there is also "Foo Ward" earlier in the QS then our matching
        logic would incorrectly match with "Foo Ward" because it contains the
        ward name "Foo"
        """
        return (
            OfficialDocument.objects.filter(
                source_url=self.source_url,
                ballot__election__election_date=self.election_date,
            )
            .select_related("ballot", "ballot__post")
            .order_by(-Length("ballot__post__label"), "ballot__post__label")
        )

    def is_matched_page_numbers_valid(self):
        """
        Validates that the matched page numbers are correct by checking they
        are sequential
        """
        # if we couldnt match any pages we still return True so that the
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

    def match_ballot_to_pages(self, post_label: str) -> str:
        """
        Given a ward name, loop over all the unmatched pages looking for the
        first match.

        Return a string in the format of:
           "1,2,3,4"

        For more on this format, see https://camelot-py.readthedocs.io/en/master/user/quickstart.html?highlight=pages#specify-page-numbers
        """
        self.clear_old_matched_pages()
        for page in self.unmatched_pages:
            page.previous_page = self.pages.get(page.page_number - 1)
            page.document_heading_set = self.document_heading_set
            page.post_label_to_match = clean_text(post_label)

            if self.matched_pages and not page.is_continuation_page:
                break

            if self.matched_pages and page.is_continuation_page:
                self.add_to_matched_pages(page)
                continue

            # no matched pages but we know this is a continuation page so dont
            # search for the post label in case of edge case such as the ward
            # name appears in a candidates address
            if page.is_continuation_page:
                continue

            if page.contains_post_label():
                self.add_to_matched_pages(page)

        if not self.is_matched_page_numbers_valid():
            matched_page_str = ",".join(
                str(number) for number in self.matched_page_numbers
            )
            if self.strict:
                raise MatchedPagesError(
                    f"Page numbers are not consecutive for {self.source_url}. Pages: {matched_page_str}. Post: {post_label}"
                )
            print(
                f"Page numbers are not consecutive for {self.source_url}. Pages: {matched_page_str}. Post: {post_label}. Skipping."
            )
            return ""

        return ",".join(str(number) for number in self.matched_page_numbers)

    def save_matched_pages(self, document: OfficialDocument):
        """
        Attemps to find matched pages and save them against the OfficialDocument
        If none are found, do nothing, unless we are in "strict" mode where we
        raise an exception for debugging purposes.
        """
        matched_pages = self.match_ballot_to_pages(
            post_label=document.ballot.post.label
        )

        if self.strict and not matched_pages:
            raise MatchedPagesError(
                f"We couldnt match any pages for {document.ballot.ballot_paper_id}"
            )

        # if we are re-parsing and matched pages changed log it
        if document.relevant_pages and matched_pages != document.relevant_pages:
            print(
                "{ballot} matched pages changed from {previously_matched} to {new_matched}".format(
                    ballot=document.ballot.ballot_paper_id,
                    previously_matched=document.relevant_pages,
                    new_matched=matched_pages or "0",
                )
            )

        if matched_pages:
            self.unmatched_documents.remove(document)

        document.relevant_pages = matched_pages
        try:
            return document.save()
        except Exception as e:
            print("Error trying to save relevant_pages, see below:")
            print(document.ballot.ballot_paper_id, document.relevant_pages)
            if self.strict:
                raise e

            document.relevant_pages = ""
            return document.save()

    def match_all_pages(self) -> None:
        """
        Loops through all associated OfficialDocument objects, and attempts to
        match its associated Ballot with pages in the PDF file. If matches are
        found, the OfficialDocument's relevant_pages field is updated.
        """
        if self.guess_all_pages:
            document = self.unmatched_documents.pop()
            document.relevant_pages = "all"
            return document.save()

        official_documents = self.unmatched_documents.copy()
        for document in official_documents:
            self.save_matched_pages(document=document)

        if self.strict and self.unmatched_documents:
            raise MatchedPagesError(
                f"Some OfficialDocument objects were unmatched for {self.source_url}"
            )
        return None

    def parse_pages(self):
        """
        Returns a dictionary where the key is the page number, and the value is
        a SOPNPageText object
        """
        pages = {}
        rsrcmgr = PDFResourceManager()

        laparams = LAParams(line_margin=0.1)

        fp = self.file

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
