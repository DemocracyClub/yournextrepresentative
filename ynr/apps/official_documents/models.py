import os
from pathlib import Path

from django.core.validators import FileExtensionValidator
from django.db import models
from django.urls import reverse
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
    if not instance.pk:
        raise ValueError(
            "ElectionSOPN.pk required. Save the instance before saving the uploaded_file."
        )
    return (
        Path("official_documents")
        / instance.election.slug
        / instance.pk
        / filename
    )


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

    class Meta:
        get_latest_by = "modified"

    def __str__(self):
        return "{} ({})".format(self.election.slug, self.source_url)


def ballot_sopn_file_name(instance: "BaseBallotSOPN", filename):
    if not instance.pk:
        raise ValueError(
            "BaseBallotSOPN.pk required. Save the instance before saving the uploaded_file."
        )
    return (
        Path("official_documents")
        / instance.ballot.ballot_paper_id
        / "sopn"
        / instance.pk
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
        validators=[FileExtensionValidator(allowed_extensions=["pdf"])],
    )

    source_url = models.URLField(
        help_text="The URL of this document", max_length=1200
    )

    class Meta:
        get_latest_by = "modified"
        abstract = True

    def __str__(self):
        return "{} ({})".format(self.ballot.ballot_paper_id, self.source_url)


class BallotSOPN(BaseBallotSOPN):
    ...


class BallotSOPNHistory(BaseBallotSOPN):
    ballot = models.ForeignKey(
        "candidates.Ballot",
        on_delete=models.CASCADE,
        related_name="sopn_history",
    )
