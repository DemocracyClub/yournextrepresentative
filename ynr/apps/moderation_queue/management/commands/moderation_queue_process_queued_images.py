from django.core.management.base import BaseCommand
from moderation_queue.models import QueuedImage


class Command(BaseCommand):
    def handle(self, **options):
        qs = QueuedImage.objects.filter(decision="undecided").exclude(
            face_detection_tried=True
        )

        for qi in qs:
            try:
                qi.normalise_image()
            except Exception as e:
                self.stderr.write(
                    f"Skipping normalise for QueuedImage {qi.id}: {e}"
                )
                continue

            try:
                qi.detect_faces()
            except Exception as e:
                self.stderr.write(
                    f"Face detection failed for QueuedImage {qi.id}: {e}"
                )
