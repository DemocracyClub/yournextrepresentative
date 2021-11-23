from io import StringIO

from django.db.models.functions import Length
from official_documents.models import OfficialDocument
from pdfminer.converter import TextConverter
from pdfminer.layout import LAParams
from pdfminer.pdfinterp import PDFPageInterpreter, PDFResourceManager
from pdfminer.pdfpage import PDFPage
from sopn_parsing.helpers.text_helpers import (
    NoTextInDocumentError,
    MatchedPagesError,
    clean_page_text,
    clean_text,
)

# Used by SOPNPageText.get_page_heading
HEADING_SIZE = 0.3

# Used by SOPNPageText.detect_top_page
CONTINUATION_THRESHOLD = 0.5


class SOPNDocument:
    def __init__(self, file, source_url, strict=False):
        """
        Represents a collection of pages from a single PDF file.
        """
        self.file = file
        self.source_url = source_url
        self.strict = strict
        self.unmatched_documents = list(
            self.all_official_documents_with_source()
        )
        self.pages = self.parse_pages()
        self.document_heading = self.pages[0].get_page_heading_set()
        self.matched_pages = []
        self.previous_page = None

        if len(self.document_heading) < 10:
            raise NoTextInDocumentError()

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
            OfficialDocument.objects.filter(source_url=self.source_url)
            .select_related("ballot", "ballot__post")
            .order_by(-Length("ballot__post__label"))
        )

    @property
    def matched_page_numbers(self):
        return [page.page_number for page in self.matched_pages]

    @property
    def unmatched_pages(self):
        return [page for page in self.pages if not page.matched]

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
        self.previous_page = page

    def clear_old_matched_pages(self):
        """
        Remove any previously set matched pages and previous page
        """
        self.matched_pages = []
        self.previous_page = None

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

            page.previous_page = self.previous_page
            page_is_continuation_page = page.is_continuation_page(
                document_heading=self.document_heading, post_label=post_label
            )
            if self.previous_page and not page_is_continuation_page:
                break

            if self.previous_page and page_is_continuation_page:
                self.add_to_matched_pages(page)
                continue

            if page.matches_ward_name(post_label):
                self.add_to_matched_pages(page)

        if not self.is_matched_page_numbers_valid():
            raise MatchedPagesError("Page numbers are not consecutive")

        return ",".join(str(number) for number in self.matched_page_numbers)

    @property
    def has_single_page_and_single_document(self) -> bool:
        """
        Return if there is only one page and one related OfficialDocument
        """
        return len(self.pages) == 1 and len(self.unmatched_documents) == 1

    def save_matched_pages(self, document: OfficialDocument):
        """
        Attemps to find matched pages and save them against the OfficialDocument
        If none are found, do nothing, unless we are in "strict" mode where we
        raise an exception for debugging purposes.
        """
        matched_pages = self.match_ballot_to_pages(
            post_label=document.ballot.post.label
        )
        if matched_pages:
            self.unmatched_documents.remove(document)
            document.relevant_pages = matched_pages
            return document.save()

        if self.strict:
            raise MatchedPagesError("We couldnt match any pages")

    def match_all_pages(self) -> None:
        """
        Loops through all associated OfficialDocument objects, and attempts to
        match its associated Ballot with pages in the PDF file. If matches are
        found, the OfficialDocument's relevant_pages field is updated.
        """
        if self.has_single_page_and_single_document:
            document = self.unmatched_documents.pop()
            document.relevant_pages = "all"
            return document.save()

        official_documents = self.unmatched_documents.copy()
        for document in official_documents:
            self.save_matched_pages(document=document)

        if self.strict and self.unmatched_documents:
            raise MatchedPagesError(
                "Some OfficialDocument objects were unmatched"
            )

    def parse_pages(self):
        pages = []
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
            pages.append(SOPNPageText(page_no, retstr.getvalue()))
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
        self.continuation_page = False
        self.matched = None
        self.document = None
        self.matched_post_label = None
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
        search_text = " ".join(words[0:threshold])
        return search_text

    def matches_ward_name(self, ward_name):
        ward = clean_text(ward_name)
        search_text = self.get_page_heading()
        wards = ward.split("/")
        for ward in wards:
            if ward in search_text:
                self.matched_post_label = ward
                return True
        return False

    def set_continuation_page(self, is_continuation_page: bool):
        """
        Marks whether this is a continuation page and conditionally stores the
        matched label from the previous page
        """
        if is_continuation_page and not self.matched_post_label:
            self.matched_post_label = self.previous_page.matched_post_label

        self.continuation_page = is_continuation_page
        return self.continuation_page

    def is_continuation_page(self, document_heading, post_label):
        """
        Take a set containing the document heading (returned from
        `get_page_heading_set`) and compare it to another heading set.
        This is done by taking the intersection of the two sets. If the length
        of the intersection set divided by the length of the provided
        document_heading set is less than CONTINUATION_THRESHOLD then we assume
        this is a "continuation" page and return True.
        If the divided number is greater than the CONTINUATION_THRESHOLD then we
        assume this is a top page and return False.
        If the headings up to the post label are identical, we assume the page
        is a continuation.
        """
        # CASE 1: Cannot be a continuation page if there is no previous page to
        # compare with
        if not self.previous_page:
            return self.set_continuation_page(is_continuation_page=False)

        post_label = clean_text(post_label)

        # CASE 2: We know the first page is never a continuation page.
        if self.page_number == 1:
            return self.set_continuation_page(is_continuation_page=False)

        # CASE 3: If the document heading is very different to the document
        # heading then we assume this is a continuation page
        similar_len = document_heading.intersection(self.get_page_heading_set())
        is_very_different_to_doc_heading = (
            len(similar_len) / len(document_heading) < CONTINUATION_THRESHOLD
        )
        if is_very_different_to_doc_heading:
            return self.set_continuation_page(is_continuation_page=True)

        # CASE 4: If the headings are more or less the same, split on the ward
        # name and see if they're identical
        previous_page_heading = self.previous_page.get_page_heading()
        previous_page_heading_up_to_ward_name = " ".join(
            previous_page_heading.partition(post_label)[0:2]
        )

        page_heading = self.get_page_heading()
        page_heading_up_to_ward_name = " ".join(
            page_heading.partition(self.previous_page.matched_post_label)[0:2]
        )

        headings_are_identical = (
            page_heading_up_to_ward_name
            == previous_page_heading_up_to_ward_name
        )
        return self.set_continuation_page(
            is_continuation_page=headings_are_identical
        )
