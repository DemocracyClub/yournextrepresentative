import io
from typing import Dict, List

from candidates.models import Ballot
from django.core.files.base import ContentFile
from django.db import transaction
from official_documents.models import (
    BallotSOPN,
    ElectionSOPN,
    PageMatchingMethods,
    add_ballot_sopn,
)
from PyPDF2 import PdfReader, PdfWriter
from PyPDF2.errors import DependencyError, PdfReadError


class PDFProcessingError(ValueError):
    """
    A generic exception to raise when various other PDF parsing exceptions are raised.
    """


def clean_matcher_data(pages):
    # This function makes some assumptions about the data
    # ensure pages has been checked with
    # ElectionSOPNMatchingView.validate_payload()
    # before passing it to this
    ballots = {
        v: []
        for k, v in pages.items()
        if v not in [ElectionSOPN.CONTINUATION, ElectionSOPN.NOMATCH]
    }
    last_ballot = None
    for k, v in pages.items():
        if v == ElectionSOPN.NOMATCH:
            continue
        if v == ElectionSOPN.CONTINUATION:
            if last_ballot is not None:
                ballots[last_ballot].append(int(k))
            continue
        ballots[v].append(int(k))
        last_ballot = v
    return ballots


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
        self, method=PageMatchingMethods.MANUAL_MATCHED, parse_ballots=True
    ):
        if self.election_sopn.pk is not None:
            BallotSOPN.objects.filter(
                election_sopn_id=self.election_sopn.pk
            ).delete()

        for ballot_paper_id, matched_pages in self.ballot_to_pages.items():
            if not matched_pages:
                continue

            pdf_pages = io.BytesIO()
            writer = PdfWriter()
            try:
                for page in matched_pages:
                    writer.add_page(self.reader.pages[page])
            except DependencyError as exception:
                raise PDFProcessingError(f"{exception}")

            writer.write(pdf_pages)
            pdf_pages.seek(0)
            pdf_content = ContentFile(
                pdf_pages.getvalue(),
                name=f"sopn-{ballot_paper_id}.pdf",
            )
            relevant_pages = ",".join([str(num) for num in matched_pages])
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
                election_sopn=self.election_sopn,
                parse=parse_ballots,
            )

            self.election_sopn.page_matching_method = method
            self.election_sopn.save()
