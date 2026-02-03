from django.conf import settings
from django.db import models
from django.db.models import JSONField
from model_utils.models import TimeStampedModel

TRUSTED_TO_BULK_ADD_GROUP_NAME = "Trusted to bulk add"


class RawPeople(TimeStampedModel):
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
    data = JSONField(default=dict)
    textract_data = JSONField(default=dict)
    source = models.CharField(max_length=512)
    source_type = models.CharField(
        choices=SOURCE_TYPES, default=SOURCE_BULK_ADD_FORM, max_length=255
    )

    def __str__(self):
        return "{} ({})".format(self.ballot.ballot_paper_id, self.source)

    def as_form_kwargs(self, parser=settings.DEFAULT_PARSING_BACKEND):
        """
        Returns a list of dicts designed for populating the BulkAddFormSet's
        initial values

        """
        data_attr = self.textract_data
        if (
            parser != settings.SOPN_PARSING_BACKENDS.TEXTRACT
            or self.source_type != self.SOURCE_PARSED_PDF
        ):
            data_attr = self.data

        if not data_attr:
            if parser == settings.SOPN_PARSING_BACKENDS.TEXTRACT and self.data:
                data_attr = self.data
            else:
                return {}
        initial = []

        for candidacy in data_attr:
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
                }
            )
        return {"initial": initial}

    @property
    def is_trusted(self):
        return self.source_type in self.TRUSTED_SOURCES

    @property
    def is_parsed_from_pdf(self):
        return self.source_type == self.SOURCE_PARSED_PDF
