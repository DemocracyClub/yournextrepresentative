from io import StringIO

from pdfminer.converter import TextConverter
from pdfminer.layout import LAParams
from pdfminer.pdfinterp import PDFResourceManager, PDFPageInterpreter
from pdfminer.pdfpage import PDFPage

from sopn_parsing.helpers.text_helpers import clean_text, NoTextInDocumentError

# Used by SOPNPageText.get_page_heading
HEADING_SIZE = 0.3

# Used by SOPNPageText.detect_top_page
CONTINUATION_THRESHOLD = 0.4


class SOPNDocument:
    def __init__(self, file_path):
        self.file_path = file_path
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

        codec = "utf-8"
        laparams = LAParams()

        fp = open(self.file_path, "rb")

        for page_no, page in enumerate(
            PDFPage.get_pages(fp, check_extractable=True), start=1
        ):
            retstr = StringIO()
            device = TextConverter(
                rsrcmgr, retstr, codec=codec, laparams=laparams
            )
            interpreter = PDFPageInterpreter(rsrcmgr, device)
            interpreter.process_page(page)
            self.pages.append(SOPNPageText(page_no, retstr.getvalue()))
            device.close()
            retstr.close()
        fp.close()

    def get_pages_by_ward_name(self, ward):
        ward = clean_text(ward)
        matched_pages = []
        for page in self.pages:
            if page.is_top_page:
                if matched_pages:
                    return matched_pages
                search_text = clean_text(page.get_page_heading())
                wards = ward.split("/")
                for ward in wards:
                    if ward in search_text:
                        matched_pages.append(page)
            else:
                if matched_pages:
                    matched_pages.append(page)
        if matched_pages:
            return matched_pages


class SOPNPageText:
    """
    Represents a single page of text contained in a PDF.
    """

    def __init__(self, page_number, text):
        self.page_number = page_number
        self.text = text
        self.is_top_page = True

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
        threshold = int(len(self.text) * HEADING_SIZE)
        search_text = self.text[0:threshold]
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
        similar_len = document_heading.intersection(self.get_page_heading_set())
        if len(similar_len) / len(document_heading) < CONTINUATION_THRESHOLD:
            self.is_top_page = False
        return self.is_top_page
