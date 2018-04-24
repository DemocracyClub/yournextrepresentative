from django.db import models

from django_extensions.db.models import TimeStampedModel

from ..constants import REPORTED_RESULT_STATUSES



class BaseResultModel(TimeStampedModel):
    class Meta:
        abstract = True
        get_latest_by = "modified"

    source = models.TextField(null=True)



class ResultStatusMixin(models.Model):
    class Meta:
        abstract = True

    is_final = models.BooleanField(default=False)
    final_source = models.TextField(null=True)

    review_status = models.CharField(blank=True, max_length=100,
        choices=REPORTED_RESULT_STATUSES)


    reviewed_by = models.ForeignKey(
        'auth.User',
        null=True,
    )
    review_source = models.TextField(null=True)
