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
