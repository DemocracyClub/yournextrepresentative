from model_utils.models import TimeStampedModel

from django.db import models


class PageNotFoundLog(TimeStampedModel):
    """
    A tiny model to track 404s. This allows us to make sure we've not forgotten
    an important redirect.

    """

    url = models.CharField(max_length=800)
    root_path = models.CharField(max_length=100)

    def save(self, **kwargs):
        self.root_path = self.url.strip("/").split("/")[0]
        return super().save(**kwargs)
