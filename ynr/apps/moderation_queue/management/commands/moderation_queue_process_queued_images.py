import json

import boto3
import sorl
from django.core.management.base import BaseCommand
from moderation_queue.helpers import convert_image_to_png
from moderation_queue.models import QueuedImage
from PIL import Image, ImageOps

try:
    from storages.backends.s3 import S3Storage
except ImportError:
    S3Storage = None

# These magic values are because the AWS API crops faces quite tightly by
# default, meaning we literally just get the face. These values are about
# right or, they are more right than the default crop.
MIN_SCALING_FACTOR = 0.7
MAX_SCALING_FACTOR = 1.3


class Command(BaseCommand):
    def handle(self, **options):
        rekognition = boto3.client("rekognition", region_name="eu-west-1")
        attributes = ["ALL"]

        qs = QueuedImage.objects.filter(decision="undecided").exclude(
            face_detection_tried=True
        )

        for qi in qs:
            try:
                pil_img = Image.open(qi.image.file)
                pil_img = ImageOps.exif_transpose(pil_img)
            except Exception as e:
                msg = "Skipping QueuedImage{id}: {error}"
                self.stdout.write(msg.format(id=qi.id, error=e))
                continue

            png_buffer = convert_image_to_png(pil_img)
            qi.image.save(qi.image.name, png_buffer)
            sorl.thumbnail.delete(qi.image.name, delete_file=False)

            try:
                storage = qi.image.storage
                if S3Storage and isinstance(storage, S3Storage):
                    rekognition_image = {
                        "S3Object": {
                            "Bucket": storage.bucket_name,
                            "Name": storage._normalize_name(qi.image.name),
                        }
                    }
                else:
                    rekognition_image = {"Bytes": png_buffer.getvalue()}
                detected = rekognition.detect_faces(
                    Image=rekognition_image, Attributes=attributes
                )
                self.set_x_y_from_response(qi, detected, options["verbosity"])
            except Exception as e:
                msg = "Skipping QueuedImage{id}: {error}"
                self.stderr.write(msg.format(id=qi.id, error=e))

            qi.face_detection_tried = True
            qi.rotation_tried = True
            qi.save()

    def get_bound(self, bound, im_size, scaling_factor):
        """
        In some situations the bound can be <0, and this breaks the DB
        constraint. Use this methd to return at least 0

        """
        bound = bound * im_size * scaling_factor
        return max(0, bound)

    def set_x_y_from_response(self, qi, detected, verbosity=0):
        if detected and detected["FaceDetails"]:
            im_width = qi.image.width
            im_height = qi.image.height
            bounding_box = detected["FaceDetails"][0]["BoundingBox"]
            qi.crop_min_x = self.get_bound(
                bound=bounding_box["Left"],
                im_size=im_width,
                scaling_factor=MIN_SCALING_FACTOR,
            )
            qi.crop_min_y = self.get_bound(
                bound=bounding_box["Top"],
                im_size=im_height,
                scaling_factor=MIN_SCALING_FACTOR,
            )
            qi.crop_max_x = self.get_bound(
                bound=bounding_box["Width"],
                im_size=im_width,
                scaling_factor=MAX_SCALING_FACTOR,
            )
            qi.crop_max_y = self.get_bound(
                bound=bounding_box["Height"],
                im_size=im_height,
                scaling_factor=MAX_SCALING_FACTOR,
            )
            qi.detection_metadata = json.dumps(detected, indent=4)

            if int(verbosity) > 1:
                self.stdout.write("Set bounds of {}".format(qi))
        else:
            self.stdout.write("Couldn't find a face in {}".format(qi))
