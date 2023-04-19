import json
from io import BytesIO

import sorl
from PIL import Image
from django.core.management.base import BaseCommand, CommandError
from moderation_queue.models import QueuedImage


class Command(BaseCommand):
    def handle(self, **options):
        any_failed = False

        qs = QueuedImage.objects.filter(decision="undecided").exclude(
            detection_metadata=""
        )

        for queued_image in qs:
            try:
                self.rotate_queued_images(
                    queued_image=queued_image,
                )
            except Exception as e:
                msg = "Skipping QueuedImage {id}: {error}"
                self.stdout.write(msg.format(id=queued_image.id, error=e))
                any_failed = True
            queued_image.save()
        if any_failed:
            raise CommandError("Broken images found (see above)")

    def rotate_queued_images(self, queued_image):
        """
        Detects the rotation of an image and returns an integer
        """
        detected = json.loads(queued_image.detection_metadata)
        if not detected["FaceDetails"]:
            self.stdout.write(
                "No face details found for image: {queued_image.id}"
            )
            return

        PILimage = Image.open(queued_image.image, formats=None)
        # Calculate the angle image is rotated by rounding the roll
        # value to the nearest multiple of 90

        roll = detected["FaceDetails"][0]["Pose"]["Roll"]
        img_rotation_angle = round(roll / 90) * 90
        rotated = PILimage.rotate(angle=img_rotation_angle, expand=True)
        buffer = BytesIO()
        rotated.save(buffer, format="PNG")
        queued_image.image.save(queued_image.image.name, buffer)
        sorl.thumbnail.delete(queued_image.image.name, delete_file=False)
        return rotated
