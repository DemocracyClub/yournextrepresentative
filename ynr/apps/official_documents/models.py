import os

from django.db import models
from django.utils.translation import ugettext_lazy as _

from popolo.models import Post
from elections.models import Election

from django_extensions.db.models import TimeStampedModel

DOCUMENT_UPLOADERS_GROUP_NAME = "Document Uploaders"


def document_file_name(instance, filename):
    return os.path.join(
        "official_documents",
        str(instance.post_id),
        filename,
    )


class OfficialDocument(TimeStampedModel):
    # TODO FK to post_election and remove the Election and Post FKs
    NOMINATION_PAPER = 'Nomination paper'

    DOCUMENT_TYPES = (
        (NOMINATION_PAPER, _('Nomination paper'), _('Nomination papers')),
    )

    election = models.ForeignKey(Election)
    document_type = models.CharField(
        blank=False,
        choices=[(d[0], d[1]) for d in DOCUMENT_TYPES],
        max_length=100)
    uploaded_file = models.FileField(
        upload_to=document_file_name, max_length=800)
    post = models.ForeignKey(Post, blank=True, null=True)
    post_election = models.ForeignKey('candidates.PostExtraElection', null=False)
    source_url = models.URLField(
        help_text=_("The page that links to this document"),
        max_length=1000,
    )

    def __str__(self):
        return "{} ({})".format(
            self.post.extra.slug,
            self.source_url,
        )

    @models.permalink
    def get_absolute_url(self):
        return ('uploaded_document_view', (), {'pk': self.pk})

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
