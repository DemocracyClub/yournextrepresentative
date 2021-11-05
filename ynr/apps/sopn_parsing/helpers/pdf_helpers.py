from io import StringIO

from pdfminer.converter import TextConverter
from pdfminer.layout import LAParams
from pdfminer.pdfinterp import PDFPageInterpreter, PDFResourceManager
from pdfminer.pdfpage import PDFPage

from sopn_parsing.helpers.text_helpers import (
    NoTextInDocumentError,
    clean_text,
    clean_page_text,
)

# Used by SOPNPageText.get_page_heading
HEADING_SIZE = 0.3

# Used by SOPNPageText.detect_top_page
CONTINUATION_THRESHOLD = 0.5


class SOPNDocument:
    def __init__(self, file):
        self.file = file
        self.pages = []
        self.parse_pages()
        self.document_heading = self.pages[0].get_page_heading_set()
        if len(self.document_heading) < 10:
            raise NoTextInDocumentError()
        self.top_pages = [
            p.page_number
            for p in self.pages
            if p.detect_top_page(self.document_heading)
        ]

    def parse_pages(self):
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
            self.pages.append(SOPNPageText(page_no, retstr.getvalue()))
            device.close()
            retstr.close()
        fp.close()

    def get_pages_by_ward_name(self, ward):
        ward = clean_text(ward)
        matched_pages = []
        for page in self.unmatched_pages():
            if page.is_top_page:
                if matched_pages:
                    return matched_pages
                search_text = page.get_page_heading()
                wards = ward.split("/")
                for ward in wards:
                    if ward in search_text:
                        page.matched = ward
                        matched_pages.append(page)
            else:
                if matched_pages:
                    page.matched = ward
                    matched_pages.append(page)
        if matched_pages:
            return matched_pages

    def unmatched_pages(self):
        return [p for p in self.pages if not p.matched]


class SOPNPageText:
    """
    Represents a single page of text contained in a PDF.
    """

    def __init__(self, page_number, text):
        self.page_number = page_number
        self.raw_text = text
        self.text = clean_page_text(text)
        self.is_top_page = True
        self.matched = None

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
        words = self.text.split(" ")
        threshold = int(len(words) * HEADING_SIZE)
        search_text = " ".join(words[0:threshold])
        search_text = search_text.replace("\n", " ")
        return search_text.lower()

    def detect_top_page(self, document_heading):
        """
        Take a set containing the document heading (returned from
        `get_page_heading_set`) and compare it to another heading set.

        This is done by taking the intersection of the two sets. If the length
        of the intersection set divided by the length of the provided
        document_heading set is less than CONTINUATION_THRESHOLD then we assume
        this is a "continuation" page and return False.

        If the divided number is greater than the CONTINUATION_THRESHOLD then we
        assume this is a top page and return True.

        """
        # We know the first page is never a continuation page.
        if self.page_number == 1:
            self.is_top_page = True
            return self.is_top_page

        similar_len = document_heading.intersection(self.get_page_heading_set())

        headings_are_identical = similar_len == document_heading

        is_continuation_page = (
            len(similar_len) / len(document_heading) < CONTINUATION_THRESHOLD
            or headings_are_identical
        )

        if is_continuation_page or not headings_are_identical:
            self.is_top_page = False

        if is_continuation_page:
            self.is_top_page = False
        return self.is_top_page
