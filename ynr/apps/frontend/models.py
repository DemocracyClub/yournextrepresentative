from django.utils.timezone import now

from django.db import models
from model_utils.models import TimeStampedModel


class SiteBannerQueryset(models.query.QuerySet):
    def live(self):
        return self.filter(published=True, show_until__gt=now())


class SiteBanner(TimeStampedModel):
    message = models.TextField(
        help_text="Markdown formatted text to show on every page"
    )
    published = models.BooleanField(default=False)
    show_until = models.DateTimeField()

    objects = SiteBannerQueryset.as_manager()

    class Meta:
        get_latest_by = "modified"
