import contextlib
import os
from pathlib import Path
from typing import List

from candidates.models import Ballot
from django.conf import settings
from django.core.files.base import ContentFile
from django.core.validators import FileExtensionValidator
from django.db import models
from django.urls import reverse
from django.utils import timezone
from django_extensions.db.models import TimeStampedModel
from sopn_parsing.models import AWSTextractParsedSOPN

DOCUMENT_UPLOADERS_GROUP_NAME = "Document Uploaders"


def document_file_name(instance, filename):
    return os.path.join(
        "official_documents", str(instance.ballot.ballot_paper_id), filename
    )


class OfficialDocument(TimeStampedModel):
    NOMINATION_PAPER = "Nomination paper"

    DOCUMENT_TYPES = (
        (NOMINATION_PAPER, "Nomination paper", "Nomination papers"),
    )

    document_type = models.CharField(
        blank=False,
        choices=[(d[0], d[1]) for d in DOCUMENT_TYPES],
        max_length=100,
    )
    uploaded_file = models.FileField(
        upload_to=document_file_name,
        max_length=800,
        validators=[FileExtensionValidator(allowed_extensions=["pdf", "docx"])],
    )
    ballot = models.ForeignKey(
        "candidates.Ballot", null=False, on_delete=models.CASCADE
    )
    source_url = models.URLField(
        help_text="The URL of this document", max_length=1000
    )
    relevant_pages = models.CharField(
        "The pages containing information about this ballot",
        max_length=50,
        default="",
    )

    class Meta:
        get_latest_by = "modified"

    def __str__(self):
        return "{} ({})".format(self.ballot.ballot_paper_id, self.source_url)

    def get_absolute_url(self):
        return reverse(
            "ballot_paper_sopn",
            kwargs={"ballot_id": self.ballot.ballot_paper_id},
        )

    @property
    def locked(self):
        """
        Is this post election locked?
        """
        return self.ballot.candidates_locked

    @property
    def lock_suggested(self):
        """
        Is there a suggested lock for this document?
        """
        return self.ballot.suggestedpostlock_set.exists()

    def get_pages(self):
        if self.relevant_pages and self.relevant_pages != "all":
            pages = self.relevant_pages.split(",")
            return sorted(int(p) for p in pages)
        return None

    @property
    def get_aws_parsed_sopn(self):
        """given an instance of an official document, return the associated aws parsed sopn"""
        return AWSTextractParsedSOPN.objects.get(sopn=self)

    @property
    def first_page_number(self):
        if self.get_pages():
            return self.get_pages()[0]
        return None

    @property
    def last_page_number(self):
        if self.get_pages():
            return self.get_pages()[-1]
        return None


def election_sopn_file_name(instance: "ElectionSOPN", filename):
    return (
        Path("official_documents")
        / instance.election.slug
        / timezone.now().isoformat()
        / filename
    )


class PageMatchingMethods(models.TextChoices):
    AUTO_MATCHED = "Automatically matched"
    MANUAL_MATCHED = "Manually matched"


class ElectionSOPN(TimeStampedModel):
    """
    Stores SOPNs that contain candidate information for each ballot in an election.

    We don't use this directly, rather we use this as a donor document for populating BallotSOPN instances.

    """

    election = models.OneToOneField(
        "elections.Election", on_delete=models.CASCADE, blank=True
    )

    uploaded_file = models.FileField(
        upload_to=election_sopn_file_name,
        max_length=1200,
        validators=[FileExtensionValidator(allowed_extensions=["pdf"])],
    )

    source_url = models.URLField(
        help_text="The URL of this document", max_length=1200
    )

    page_matching_method = models.CharField(
        max_length=255, choices=PageMatchingMethods.choices, null=True
    )

    replacement_reason = models.CharField(
        verbose_name="Reason for replacement",
        help_text="Please be as descriptive as possible to explain why the replacement SOPN is needed",
        max_length=255,
        blank=True,
    )

    class Meta:
        get_latest_by = "modified"

    def __str__(self):
        return "{} ({})".format(self.election.slug, self.source_url)

    def get_absolute_url(self):
        return reverse(
            "election_sopn",
            kwargs={"election_id": self.election.slug},
        )

    @property
    def pages_matched(self):
        return (
            bool(self.page_matching_method)
            and not self.election.ballot_set.filter(
                sopn__relevant_pages__isnull=True
            ).exists()
        )


def ballot_sopn_file_name(instance: "BaseBallotSOPN", filename):
    return (
        Path("official_documents")
        / instance.ballot.ballot_paper_id
        / "sopn"
        / timezone.now().isoformat()
        / filename
    )


class BaseBallotSOPN(TimeStampedModel):
    """
    An abstract class used by BallotSOPN and BallotSOPNHistory. Used to keep both models in sync.

    """

    ballot = models.OneToOneField(
        "candidates.Ballot", on_delete=models.CASCADE, related_name="sopn"
    )

    # Don't add `ballot` here as we want different related names for each model
    uploaded_file = models.FileField(
        upload_to=ballot_sopn_file_name,
        max_length=1200,
        validators=[
            FileExtensionValidator(
                allowed_extensions=["pdf", "jpeg", "jpg", "png"]
            )
        ],
    )

    source_url = models.URLField(
        help_text="The URL of this document", max_length=1200
    )

    relevant_pages = models.CharField(
        max_length=20,
        help_text="The pages in the ElectionSOPN that relate to this Ballot",
        default="all",
    )

    replacement_reason = models.CharField(
        verbose_name="Reason for replacement",
        help_text="Please be as descriptive as possible to explain why the replacement SOPN is needed",
        max_length=255,
        blank=True,
    )

    withdrawal_detected = models.BooleanField(default=False)

    class Meta:
        get_latest_by = "modified"
        abstract = True

    def __str__(self):
        return "{} ({})".format(self.ballot.ballot_paper_id, self.source_url)

    @property
    def first_page_int(self):
        return min(self.page_number_list)

    @property
    def page_number_list(self) -> List[int]:
        return [int(i) for i in self.relevant_pages.split(",") if i != "all"]

    @property
    def one_based_relevant_pages(self):
        return ", ".join([str(i + 1) for i in self.page_number_list])


class BallotSOPN(BaseBallotSOPN):
    def get_absolute_url(self):
        return reverse(
            "ballot_paper_sopn",
            kwargs={"ballot_id": self.ballot.ballot_paper_id},
        )

    def parse(self):
        """
        Runs code that is needed to parse this SOPN.

        When run, this should kick off the process that ends up in a set of models
        that can be used by the bulk adding application.

        The actual implementation of the parsing (e.g the backends that are used,
        and async invocations) shouldn't matter here, the key point is that this is
        the front door.

        """

        from sopn_parsing.helpers.extract_tables import extract_ballot_table
        from sopn_parsing.helpers.textract_helpers import (
            NotUsingAWSException,
            TextractSOPNHelper,
        )

        # Pull out the tables from PDFs

        # AWS Textract
        # Don't break if we're not on AWS
        with contextlib.suppress(NotUsingAWSException):
            textract_helper = TextractSOPNHelper(self)
            # Start detection isn't going to populate anything for a while.
            # There's a cron job that should pick up the result and carry on parsing later.
            textract_helper.start_detection()

        if getattr(
            settings, "CAMELOT_ENABLED", False
        ) and self.uploaded_file.name.endswith(".pdf"):
            # Camelot
            extract_ballot_table(self.ballot)


class BallotSOPNHistory(BaseBallotSOPN):
    ballot = models.ForeignKey(
        "candidates.Ballot",
        on_delete=models.CASCADE,
        related_name="sopn_history",
    )


def add_ballot_sopn(
    ballot: Ballot,
    pdf_content: ContentFile,
    source_url: str,
    relevant_pages: str = "all",
    replacement_reason=None,
    parse=True,
):
    """
    Manage creating BallotSOPNs with history
    """
    if not replacement_reason:
        replacement_reason = ""

    BallotSOPNHistory.objects.create(
        ballot=ballot,
        relevant_pages=relevant_pages,
        uploaded_file=pdf_content,
        source_url=source_url,
        replacement_reason=replacement_reason,
    )

    BallotSOPN.objects.filter(ballot=ballot).delete()
    ballot_sopn: BallotSOPN = BallotSOPN.objects.create(
        ballot=ballot,
        relevant_pages=relevant_pages,
        uploaded_file=pdf_content,
        source_url=source_url,
        replacement_reason=replacement_reason,
    )
    if parse:
        ballot_sopn.parse()
    return ballot_sopn
