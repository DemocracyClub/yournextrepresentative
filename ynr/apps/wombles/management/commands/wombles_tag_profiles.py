import contextlib
import datetime

from candidates.models.db import ActionType
from django.core.management.base import BaseCommand
from django.db.models import Count
from django.utils import timezone
from wombles.models import WombleProfile, WombleTags


class Command(BaseCommand):
    def handle(self, *args, **options):
        self.add_inactive()
        self.add_superwombles()
        self.add_results_raccoon()
        self.add_photo_uploader()
        self.add_photo_editor()

    def add_tag(self, tag_label, qs):
        with contextlib.suppress(WombleTags.DoesNotExist):
            WombleTags.objects.get(label=tag_label).delete()

        tag = WombleTags.objects.create(label=tag_label)
        tag.wombleprofile_set.add(*qs)

    def add_inactive(self):
        inactive_days_threshold = 400
        inactive_date = timezone.now() - datetime.timedelta(
            days=inactive_days_threshold
        )
        qs = WombleProfile.objects.exclude(
            user__loggedaction__created__gt=inactive_date
        )
        self.add_tag("inactive", qs)

    def add_superwombles(self):
        superwombles_threshold = 1000

        qs = WombleProfile.objects.annotate(
            edits=Count("user__loggedaction")
        ).filter(edits__gte=superwombles_threshold)

        self.add_tag("superwomble", qs)

    def add_results_raccoon(self):
        threshold = 20

        actions = [
            ActionType.SET_CANDIDATE_ELECTED,
            ActionType.SET_CANDIDATE_NOT_ELECTED,
            ActionType.ENTERED_RESULTS_DATA,
        ]

        qs = WombleProfile.objects.annotate(
            edits=Count("user__loggedaction")
        ).filter(
            user__loggedaction__action_type__in=actions, edits__gte=threshold
        )

        self.add_tag("Results Raccoon", qs)

    def add_photo_uploader(self):
        threshold = 10

        actions = ["photo-upload"]

        qs = WombleProfile.objects.annotate(
            edits=Count("user__loggedaction")
        ).filter(
            user__loggedaction__action_type__in=actions, edits__gte=threshold
        )

        self.add_tag("Photo Uploader", qs)

    def add_photo_editor(self):
        threshold = 10

        actions = ["photo-approve", "photo-ignore", "photo-reject"]

        qs = WombleProfile.objects.annotate(
            edits=Count("user__loggedaction")
        ).filter(
            user__loggedaction__action_type__in=actions, edits__gte=threshold
        )

        self.add_tag("Photo Editor", qs)
