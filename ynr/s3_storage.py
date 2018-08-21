from storages.backends.s3boto3 import S3Boto3Storage
from django.contrib.staticfiles.storage import ManifestFilesMixin
from pipeline.storage import PipelineMixin

from django.conf import settings


class StaticStorage(PipelineMixin, ManifestFilesMixin, S3Boto3Storage):
    """
    Store static files on S3 at STATICFILES_LOCATION, post-process with pipeline
    and then create manifest files for them.
    """

    location = settings.STATICFILES_LOCATION


class MediaStorage(S3Boto3Storage):
    """
    Store media files on S3 at MEDIAFILES_LOCATION
    """

    location = settings.MEDIAFILES_LOCATION

    @property
    def base_url(self):
        """
        This is a small hack around the fact that Django Storages dosn't
        provide the same methods as FileSystemStorage.

        `base_url` is missing from their implementation of the storage class,
        so we emulate it here by calling URL with an empty key name.
        """
        return self.url("")
