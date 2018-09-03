from django.utils import timezone

from django.db import models


class PartyQuerySet(models.QuerySet):
    def active_for_date(self, date=None):
        if not date:
            date = timezone.now()
        qs = self.filter(date_registered__lte=date)
        qs = qs.filter(
            models.Q(date_deregistered__gte=date)
            | models.Q(date_deregistered=None)
        )
        return qs

    def current(self):
        return self.active_for_date()
