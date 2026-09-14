import re

import boto3
from django.conf import settings
from django.core.management.base import BaseCommand
from people.models import PersonImage

PATTERNS = [
    # numeric e.g: media/images/images/920.png
    re.compile(r"^media/images/images/\d+\.png$"),
    # uuid e.g: media/images/images/9271-c2f10a81-e6df-4725-9a3f-1c06152adb98.png
    re.compile(
        r"^media/images/images/\d+-[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}\.png$"
    ),
    # 24-character hex string e.g: images/5481e86fb150e238702c05cd.png
    re.compile(r"^media/images/[0-9a-f]{24}\.(?:png|jpg)$"),
    # numeric with suffix e.g: media/images/images/35525_mduTdlE.png
    re.compile(r"^media/images/images/\d+_[A-Za-z0-9]{7}\.(?:png|jpg)$"),
    # with people prefix e.g: media/images/people/9874/e1a70a9e-8d83-4291-b894-a468eae14d76.png
    re.compile(r"^media/images/people/.+\.png$"),
]


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument(
            "action",
            choices=["list", "delete"],
            help="Action to perform",
        )

    def handle(self, *args, **kwargs):
        action = kwargs["action"]

        s3 = boto3.client("s3", region_name=settings.AWS_S3_REGION_NAME)
        bucket_name = settings.AWS_STORAGE_BUCKET_NAME

        response = s3.list_objects_v2(
            Bucket=bucket_name, Prefix="media/images/"
        )

        self.stdout.write("Listing orphan images..")

        linked_images_count = 0
        ignored_images_count = 0
        orphan_images = []

        while True:
            for obj in response.get("Contents", []):
                if any(pattern.match(obj["Key"]) for pattern in PATTERNS):
                    try:
                        filename = obj["Key"].removeprefix("media/")
                        PersonImage.objects.get(image=filename)
                        linked_images_count = linked_images_count + 1
                    except PersonImage.DoesNotExist:
                        self.stdout.write(obj["Key"])
                        orphan_images.append(obj["Key"])
                else:
                    ignored_images_count = ignored_images_count + 1

            if response.get("IsTruncated"):
                response = s3.list_objects_v2(
                    Bucket=bucket_name,
                    ContinuationToken=response["NextContinuationToken"],
                    Prefix="media/images/people/",
                )
            else:
                break

        orphan_images_count = len(orphan_images)
        self.stdout.write(f"ignored {ignored_images_count} images")
        self.stdout.write(f"found {linked_images_count} linked images")
        self.stdout.write(f"found {orphan_images_count} orphan images")

        if action == "delete":
            self.stdout.write("Deleting orphan images..")
            for obj in orphan_images:
                s3.delete_object(Bucket=bucket_name, Key=obj)
            self.stdout.write(f"Deleted {orphan_images_count} orphan images")
