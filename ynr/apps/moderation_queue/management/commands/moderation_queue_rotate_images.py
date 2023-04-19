import json
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

        for qi in qs:
            try:
                detected = json.loads(qi.detection_metadata)
                if len(detected["FaceDetails"]) > 0:
                    self.rotate_queued_images(image=qi.image, detected=detected)
                    sorl.thumbnail.delete(qi.image.name, delete_file=False)
                else:
                    msg = "No face details found for image: {qi.image.id}"
                    self.stdout.write(msg)
            except Exception as e:
                msg = "Skipping QueuedImage{id}: {error}"
                self.stdout.write(msg.format(id=qi.id, error=e))
                any_failed = True
            qi.save()
        if any_failed:
            raise CommandError("Broken images found (see above)")

    def rotate_queued_images(self, image, detected):
        """
        Detects the rotation of an image and returns an integer
        """
        image_path = image.path
        image = Image.open(image, formats=None)
        # Calculate the angle image is rotated by rounding the roll
        # value to the nearest multiple of 90
        roll = detected["FaceDetails"][0]["Pose"]["Roll"]
        img_rotation_angle = round(roll / 90) * 90
        rotated = image.rotate(angle=img_rotation_angle, expand=True)
        rotated.save(image_path, "PNG")
        image.close()
        return rotated
