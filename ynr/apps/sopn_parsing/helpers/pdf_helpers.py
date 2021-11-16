from io import StringIO
from typing import List, Dict, Tuple

from django.db.models.functions import Length

from candidates.models import Ballot
from official_documents.models import OfficialDocument
from pdfminer.converter import TextConverter
from pdfminer.layout import LAParams
from pdfminer.pdfinterp import PDFPageInterpreter, PDFResourceManager
from pdfminer.pdfpage import PDFPage
from sopn_parsing.helpers.text_helpers import (
    NoTextInDocumentError,
    clean_page_text,
    clean_text,
)

# Used by SOPNPageText.get_page_heading
HEADING_SIZE = 0.3

# Used by SOPNPageText.detect_top_page
CONTINUATION_THRESHOLD = 0.5


class SOPNDocument:
    def __init__(self, file, all_documents_with_source):
        self.file = file
        self.unmatched_documents = set(doc for doc in all_documents_with_source)
        self.matched_documents = set()
        self.pages = self.parse_pages()
        self.document_heading = self.pages[0].get_page_heading_set()

        if len(self.document_heading) < 10:
            raise NoTextInDocumentError()

    @property
    def matched_pages(self):
        return [p for p in self.pages if p.matched]

    @property
    def unmatched_pages(self):
        return [p for p in self.pages if not p.matched]

    def match_ballot_to_pages(self, ballot: Ballot) -> str:
        """
        Given a ballot object, loop over all the unmatched pages looking for the
        first match.

        Return a string in the format of:
           "1,2,3,4"
        OR
            "all"

        For more on this format, see https://camelot-py.readthedocs.io/en/master/user/quickstart.html?highlight=pages#specify-page-numbers
        """
        page_numbers = []
        previous_page = None
        for page in self.unmatched_pages:
            post_label = ballot.post.label
            if previous_page:
                if page.is_continuation_page(
                    self.document_heading, previous_page, post_label
                ):
                    page_numbers.append(page.page_number)
                else:
                    break
            else:
                if page.matches_ward_name(post_label):
                    page_numbers.append(page.page_number)
                    page.matched = True
                    previous_page = page
        return ",".join([str(page_num) for page_num in page_numbers])

    def match_all_pages(self) -> List[Tuple[OfficialDocument, str]]:
        """

        [
            (doc, "123"),
            (doc, "456"),
        ]

        :return:
        """
        if len(self.pages) == 1 and len(self.unmatched_documents) == 1:
            return [(self.unmatched_documents.pop(), "all")]

        docs_by_sorted_ballot_label = sorted(
            self.unmatched_documents,
            key=lambda doc: len(doc.ballot.post.label),
            reverse=True,
        )
        matched_documents = []
        for doc in docs_by_sorted_ballot_label:
            matched_pages = self.match_ballot_to_pages(doc.ballot)
            if matched_pages:
                matched_documents.append((doc, matched_pages))
                # Mark this document as matched
                self.unmatched_documents.remove(doc)
                self.matched_documents.add(doc)
            else:
                continue
                # TODO: do we want to raise here so we know when we've not matched?
                # Consider passing this in as an option, so we can raise in
                # "strict mode" but not in production?
        if self.unmatched_documents:
            raise Exception("Exception: unmatched documents")
        return matched_documents

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

    def set_continuation_page(self, value, previous_page=None):
        self.continuation_page = value
        if value:
            if not self.matched_post_label:
                self.matched_post_label = previous_page.matched_post_label

        return self.continuation_page

    def is_continuation_page(self, document_heading, previous_page, post_label):
        """
        TODO: review this doc string
        Take a set containing the document heading (returned from
        `get_page_heading_set`) and compare it to another heading set.

        This is done by taking the intersection of the two sets. If the length
        of the intersection set divided by the length of the provided
        document_heading set is less than CONTINUATION_THRESHOLD then we assume
        this is a "continuation" page and return False.

        If the divided number is greater than the CONTINUATION_THRESHOLD then we
        assume this is a top page and return True.

        """
        post_label = clean_text(post_label)

        # CASE 1: We know the first page is never a continuation page.
        if self.page_number == 1:
            return self.set_continuation_page(False)

        # CASE 2: If the document heading is very different to the document
        # heading then we assume this is a continuation page
        similar_len = document_heading.intersection(self.get_page_heading_set())
        is_very_different_to_doc_heading = (
            len(similar_len) / len(document_heading) < CONTINUATION_THRESHOLD
        )
        if is_very_different_to_doc_heading:
            return self.set_continuation_page(True, previous_page)

        # CASE 3: If the headings are more or less the same, split on the ward
        # name and see if they're identical
        previous_page_heading = previous_page.get_page_heading()
        previous_page_heading_up_to_ward_name = " ".join(
            previous_page_heading.partition(post_label)[0:2]
        )

        page_heading = self.get_page_heading()
        page_heading_up_to_ward_name = " ".join(
            page_heading.partition(previous_page.matched_post_label)[0:2]
        )

        headings_are_identical = (
            page_heading_up_to_ward_name
            == previous_page_heading_up_to_ward_name
        )

        if headings_are_identical:
            return self.set_continuation_page(True, previous_page)
