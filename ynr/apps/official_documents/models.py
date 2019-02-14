import os

from django.db import models
from django.utils.translation import ugettext_lazy as _
from django.core.urlresolvers import reverse

from popolo.models import Post
from elections.models import Election

from django_extensions.db.models import TimeStampedModel

DOCUMENT_UPLOADERS_GROUP_NAME = "Document Uploaders"


def document_file_name(instance, filename):
    return os.path.join(
        "official_documents",
        str(instance.post_election.ballot_paper_id),
        filename,
    )


class OfficialDocument(TimeStampedModel):
    NOMINATION_PAPER = "Nomination paper"

    DOCUMENT_TYPES = (
        (NOMINATION_PAPER, _("Nomination paper"), _("Nomination papers")),
    )

    document_type = models.CharField(
        blank=False,
        choices=[(d[0], d[1]) for d in DOCUMENT_TYPES],
        max_length=100,
    )
    uploaded_file = models.FileField(
        upload_to=document_file_name, max_length=800
    )
    post_election = models.ForeignKey(
        "candidates.PostExtraElection", null=False
    )
    source_url = models.URLField(
        help_text=_("The page that links to this document"), max_length=1000
    )
    relevant_pages = models.CharField(
        "The pages containing information about this ballot",
        max_length=50,
        null=True,
    )

    class Meta:
        get_latest_by = "modified"

    def __str__(self):
        return "{} ({})".format(
            self.post_election.ballot_paper_id, self.source_url
        )

    def get_absolute_url(self):
        return reverse(
            "ballot_paper_sopn",
            kwargs={"ballot_id": self.post_election.ballot_paper_id},
        )

    @property
    def locked(self):
        """
        Is this post election locked?
        """
        return self.post_election.candidates_locked

    @property
    def lock_suggested(self):
        """
        Is there a suggested lock for this document?
        """
        return self.post_election.suggestedpostlock_set.exists()

    def get_pages(self):
        if self.relevant_pages and not self.relevant_pages == "all":
            pages = self.relevant_pages.split(",")
            return sorted(int(p) for p in pages)

    @property
    def first_page_number(self):
        if self.get_pages():
            return self.get_pages()[0]

    @property
    def last_page_number(self):
        if self.get_pages():
            return self.get_pages()[-1]
