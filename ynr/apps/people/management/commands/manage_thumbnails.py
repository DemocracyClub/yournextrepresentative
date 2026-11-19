from unittest import mock
from urllib.parse import unquote, urlparse

import boto3
from django.conf import settings
from django.core.management.base import BaseCommand
from people.api.next.serializers import PersonSerializer
from people.models import Person
from sorl.thumbnail import default as sorl_default
from sorl.thumbnail.base import ThumbnailBackend
from sorl.thumbnail.images import ImageFile

CACHE_PREFIX = f"{settings.MEDIAFILES_LOCATION}/cache/"


class NameComputed(Exception):
    def __init__(self, name):
        self.name = name


class NameOnlyBackend(ThumbnailBackend):
    """
    Computes the thumbnail name sorl would use, but stops before it reads the
    source image, writes a thumbnail to storage or writes to the sorl kvstore.

    This prevents side-effects when running this command.

    sorl's default get_thumbnail() does all of those on a cache miss. Writing a
    kvstore entry for a thumbnail that was never created would make sorl serve
    a missing file later.
    """

    def _get_thumbnail_filename(self, source, geometry_string, options):
        raise NameComputed(
            super()._get_thumbnail_filename(source, geometry_string, options)
        )

    def get_thumbnail(self, file_, geometry_string, **options):
        try:
            return super().get_thumbnail(file_, geometry_string, **options)
        except NameComputed as e:
            return ImageFile(e.name, sorl_default.storage)


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument(
            "action",
            choices=["list", "delete"],
            help="Action to perform",
        )

    def url_to_key(self, url):
        if not url:
            return None
        return unquote(urlparse(url).path).lstrip("/")

    def get_keys_to_keep(self):
        keep = set()
        serializer = PersonSerializer()

        # patch sorl with NameOnlyBackend
        # to prevent side-effects
        with mock.patch.object(
            sorl_default.backend, "_wrapped", NameOnlyBackend()
        ):
            for person in Person.objects.all().iterator():
                urls = [
                    person.get_display_image_url(),
                    serializer.get_thumbnail(person),
                ]
                for url in urls:
                    key = self.url_to_key(url)
                    # Ignores non-thumbnail URLs such as the static blank-person image
                    if key and key.startswith(CACHE_PREFIX):
                        keep.add(key)

        return keep

    def get_keys_to_remove(self, s3, bucket_name, keep):
        paginator = s3.get_paginator("list_objects_v2")
        for page in paginator.paginate(Bucket=bucket_name, Prefix=CACHE_PREFIX):
            for obj in page.get("Contents", []):
                if obj["Key"] not in keep:
                    yield obj["Key"]

    def handle(self, *args, **kwargs):
        action = kwargs["action"]

        s3 = boto3.client("s3", region_name=settings.AWS_S3_REGION_NAME)
        bucket_name = settings.AWS_STORAGE_BUCKET_NAME

        self.stdout.write("Finding thumbnails to keep..")
        keep = self.get_keys_to_keep()

        if action == "list":
            for key in sorted(keep):
                self.stdout.write(key)
        self.stdout.write(f"found {len(keep)} thumbnails to keep")

        self.stdout.write("Finding unused thumbnails..")
        remove_count = 0
        batch = []

        for key in self.get_keys_to_remove(s3, bucket_name, keep):
            remove_count = remove_count + 1

            if action == "delete":
                batch.append({"Key": key})
                # delete_objects accepts at most 1000 keys per request
                if len(batch) == 1000:
                    s3.delete_objects(
                        Bucket=bucket_name, Delete={"Objects": batch}
                    )
                    batch = []
            else:
                self.stdout.write(key)

        if action == "delete":
            if batch:
                s3.delete_objects(Bucket=bucket_name, Delete={"Objects": batch})
            self.stdout.write(f"Deleted {remove_count} unused thumbnails")

            self.stdout.write("Clearing sorl cache..")
            sorl_default.kvstore.clear()
            self.stdout.write("Cleared sorl cache")
        else:
            self.stdout.write(f"found {remove_count} unused thumbnails")
