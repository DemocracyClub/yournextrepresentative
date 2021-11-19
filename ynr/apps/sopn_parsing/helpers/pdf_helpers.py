from io import StringIO
from typing import List, Tuple

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
    def __init__(self, file, source_url):
        """
        Represents a collection of pages from a single PDF file.
        """
        self.file = file
        self.source_url = source_url
        self.unmatched_documents = list(
            self.all_official_documents_with_source()
        )
        self.matched_documents = []
        self.pages = self.parse_pages()
        self.document_heading = self.pages[0].get_page_heading_set()

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
    def matched_pages(self):
        return [p for p in self.pages if p.matched]

    @property
    def unmatched_pages(self):
        return [p for p in self.pages if not p.matched]

    def validate_page_numbers(self, page_numbers):
        if len(page_numbers) == 1:
            return True
        page_numbers = [page for page in page_numbers]
        lower = min(page_numbers)
        upper = max(page_numbers) + 1

        assert page_numbers == list(range(lower, upper))

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
        if not page_numbers:
            return ""
        if self.validate_page_numbers(page_numbers):
            return ",".join(str(p) for p in page_numbers)
        else:
            raise ValueError("Page numbers are not consecutive")

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

        official_documents = self.unmatched_documents.copy()
        matched_documents = []
        for doc in official_documents:
            matched_pages = self.match_ballot_to_pages(doc.ballot)
            if matched_pages:
                matched_documents.append((doc, matched_pages))
                # Mark this document as matched
                self.unmatched_documents.remove(doc)
                self.matched_documents.append(doc)
            else:
                continue
                # TODO: do we want to raise here so we know when we've not matched?
                # Consider passing this in as an option, so we can raise in
                # "strict mode" but not in production?
        if self.unmatched_documents:
            raise Exception("Unmatched documents")
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

        # TO DO: multipage sopns with multiple wards where headings
        # are close but not identical
        # for example (`/local.luton.high-town.by.2021-05-06/`)
        # can we assume if the page_heading_up_to_ward_name is
        # greater or less than the previous_page_heading_up_to_ward_name?
        # if so, we can use this to determine if the page is a continuation
        # Q: Should we only ever you use headings up to ward names
        # as the basis for determining if the page is a continuation?

        if headings_are_identical:
            return self.set_continuation_page(True, previous_page)
