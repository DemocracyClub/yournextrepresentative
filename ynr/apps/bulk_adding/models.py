from datetime import timedelta

from django.conf import settings
from django.db import models
from django.db.models import JSONField
from django.utils.timezone import now
from model_utils.models import TimeStampedModel

BULK_ADD_CLAIM_TIMEOUT = timedelta(minutes=5)

TRUSTED_TO_BULK_ADD_GROUP_NAME = "Trusted to bulk add"


class RawPeople(TimeStampedModel):
    class AlreadyClaimedError(Exception):
        pass

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
    SOURCE_PARSED_PDF = "parsed_pdf"

    SOURCE_TYPES = (
        (SOURCE_BULK_ADD_FORM, "Bulk Add form"),
        (SOURCE_COUNCIL_CSV, "Council CSV"),
        (SOURCE_PARSED_PDF, "Parsed from a PDF"),
    )

    # Sources that we trust enough to just review, not ask a user
    # to edit (edit option always there)
    TRUSTED_SOURCES = (SOURCE_COUNCIL_CSV, SOURCE_BULK_ADD_FORM)

    ballot = models.OneToOneField("candidates.Ballot", on_delete=models.CASCADE)
    textract_data = JSONField(default=dict)
    source = models.CharField(max_length=512)
    source_type = models.CharField(
        choices=SOURCE_TYPES, default=SOURCE_BULK_ADD_FORM, max_length=255
    )
    reconciled_data = JSONField(default=list)
    claimed_at = models.DateTimeField(null=True, blank=True)
    claimed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="+",
    )

    def __str__(self):
        return "{} ({})".format(self.ballot.ballot_paper_id, self.source)

    def as_form_kwargs(self):
        """
        Returns a list of dicts designed for populating the BulkAddFormSet's
        initial values

        """
        initial = []
        for candidacy in self.textract_data:
            party_id = candidacy["party_id"]
            description_id = candidacy.get("description_id")
            if description_id:
                party_id = f"{party_id}__{description_id}"

            initial.append(
                {
                    "name": candidacy["name"],
                    "sopn_last_name": candidacy.get("sopn_last_name", ""),
                    "sopn_first_names": candidacy.get("sopn_first_names", ""),
                    "party": [party_id, party_id],
                    "source": self.source,
                    "previous_party_affiliations": candidacy.get(
                        "previous_party_affiliations", []
                    ),
                    "party_list_position": candidacy.get("party_list_position"),
                }
            )
        return {"initial": initial}

    def claim(self, user):
        cutoff = now() - BULK_ADD_CLAIM_TIMEOUT
        updated = (
            RawPeople.objects.filter(pk=self.pk)
            .filter(
                models.Q(claimed_at__isnull=True)
                | models.Q(claimed_at__lte=cutoff)
                # Allow users to update a claim for each page they visit
                | models.Q(claimed_by=user)
            )
            .update(claimed_at=now(), claimed_by=user)
        )
        self.refresh_from_db(fields=["claimed_at", "claimed_by"])
        if not updated and self.claimed_by_id != user.pk:
            raise RawPeople.AlreadyClaimedError()

    def has_active_claim(self):
        if not self.claimed_at:
            return False
        return (now() - self.claimed_at) < BULK_ADD_CLAIM_TIMEOUT

    def is_claimed_by_another_user(self, user):
        if not self.claimed_at or not self.claimed_by_id:
            return False
        if self.claimed_by_id == user.pk:
            return False
        return self.has_active_claim()

    @property
    def is_trusted(self):
        return self.source_type in self.TRUSTED_SOURCES

    @property
    def is_parsed_from_pdf(self):
        return self.source_type == self.SOURCE_PARSED_PDF
