import json
from io import BytesIO

import sorl
from django.core.management.base import BaseCommand, CommandError
from moderation_queue.models import QueuedImage
from PIL import Image

# These magic values are because the AWS API crops faces quite tightly by
# default, meaning we literally just get the face. These values are about
# right or, they are more right than the default crop.
MIN_SCALING_FACTOR = 0.7
MAX_SCALING_FACTOR = 1.3


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
                msg = "Skipping QueuedImage{id}: {error}"
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
            return None
        PILimage = Image.open(queued_image.image, formats=None)
        # Calculate the angle image is rotated by rounding the roll
        # value to the nearest multiple of 90
        roll = detected["FaceDetails"][0]["Pose"]["Roll"]
        img_rotation_angle = round(roll / 90) * 90
        rotated = PILimage.rotate(angle=img_rotation_angle, expand=True)
        buffer = BytesIO()
        rotated.save(buffer, "PNG")
        queued_image.image.save(queued_image.image.name, buffer)
        queued_image.rotation_tried = True
        sorl.thumbnail.delete(queued_image.image.name, delete_file=False)
        return queued_image
