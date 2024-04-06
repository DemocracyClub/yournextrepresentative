from candidates.models import Ballot
from django.db import models
from django.db.models import Count
from django_extensions.db.models import TimeStampedModel


def get_attention_needed_posts():
    qs = Ballot.objects.current_or_future()
    qs = qs.select_related("election", "post")
    qs = qs.annotate(count=Count("membership"))
    return qs.order_by("count", "election__name", "post__label")


class ElectionReport(TimeStampedModel):
    election_type = models.CharField(max_length=20)
    election_date = models.DateField()
    title = models.CharField(max_length=255)

    class Meta:
        unique_together = ("election_type", "election_date")

    def __str__(self):
        return f"{self.election_type}: {self.election_date}"
