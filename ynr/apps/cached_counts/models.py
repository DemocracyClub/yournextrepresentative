from candidates.models import Ballot
from django.db import models
from django.db.models import Count, TextChoices
from django.urls import reverse
from django_extensions.db.models import TimeStampedModel


def get_attention_needed_posts():
    qs = Ballot.objects.current_or_future()
    qs = qs.select_related("election", "post")
    qs = qs.annotate(count=Count("membership"))
    return qs.order_by("count", "election__name", "post__label")


class ElectionTypeChoices(TextChoices):
    PARL = "parl", "parl"
    NIA = "nia", "nia"
    SENEDD = "senedd", "senedd"
    SP = "sp", "sp"
    GLA = "gla", "gla"
    LOCAL = "local", "local"
    PCC = "pcc", "pcc"
    MAYOR = "mayor", "mayor"


class ElectionReport(TimeStampedModel):
    election_type = models.CharField(
        max_length=20, choices=ElectionTypeChoices.choices
    )
    election_date = models.DateField()
    title = models.CharField(max_length=255)

    class Meta:
        unique_together = ("election_type", "election_date")

    def __str__(self):
        return f"{self.election_type}: {self.election_date}"

    def get_absolute_url(self):
        return reverse(
            "election_report_view",
            args=[f"{self.election_type}-{self.election_date}"],
        )
