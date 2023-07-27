from django.db import models
from django.utils.translation import gettext_lazy as _
from django_extensions.db.fields import ModificationDateTimeField
from django_extensions.db.models import TimeStampedModel


class EEModifiedMixin(TimeStampedModel):
    """
    Inherits from TimeStampedModel to include timestamps, but also
    adds ee_modified field to a model. This is stored when the
    EEImporter runs. It is used to determine if there have been
    changes made to the object in EveryElection that need to be
    imported.
    This is distinct from the the `modified` value that is stored
    whenever an object is saved in YNR to avoid a situation where
    changes have been made in EE since the last import, but are older
    than a change made in YNR. In that situation, if the 'modified'
    value was used to determine if changes had been made in EE we
    it would return False, so we would miss out on those changes.
    """

    modified = ModificationDateTimeField(_("modified"), db_index=True)
    ee_modified = models.DateTimeField(
        null=True, blank=True, help_text="Stores the modified timestamp from EE"
    )

    class Meta:
        get_latest_by = "modified"
        abstract = True
