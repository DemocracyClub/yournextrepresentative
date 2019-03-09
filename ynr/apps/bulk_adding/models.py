from django.db import models
from model_utils.models import TimeStampedModel

TRUSTED_TO_BULK_ADD_GROUP_NAME = "Trusted to bulk add"


class RawBallotInput(TimeStampedModel):
    """
    Store a JSON representation of a ballot.

    Used as a form of cache for populating the form that adds or de-duplicates
    candidates.

    These models can be created in a few ways:

    1. People typing in information from a PDF
    2. A CSV that is given to us by a council

    In other words, some source where a human has asserted that the ballot
    contains these nominations.

    `data` is a JSON encoded list of dicts, where each item dict contains `name`
    `party_id` and optional `description_id` keys.

    The life time of this model is from the point of input to the point where
    the import is validated and each item in the list is turned in to a
    candidacy.

    """

    SOURCE_COUNCIL_CSV = "council_csv"
    SOURCE_BULK_ADD_FORM = "bulk_add_form"

    SOURCE_TYPES = (
        (SOURCE_BULK_ADD_FORM, "Bulk Add form"),
        (SOURCE_COUNCIL_CSV, "Council CSV"),
    )

    # Sources that we trust enough to just review, not ask a user
    # to edit (edit option always there)
    TRUSTED_SOURCES = (SOURCE_COUNCIL_CSV, SOURCE_BULK_ADD_FORM)

    ballot = models.OneToOneField("candidates.PostExtraElection")
    data = models.TextField()
    source = models.CharField(max_length=255)
    source_type = models.CharField(
        choices=SOURCE_TYPES, default=SOURCE_BULK_ADD_FORM, max_length=255
    )

    def __str__(self):
        return "{} ({})".format(self.ballot.ballot_paper_id, self.source)
