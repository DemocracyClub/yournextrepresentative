import os

from storages.backends.s3boto3 import S3Boto3Storage, SpooledTemporaryFile
from django.contrib.staticfiles.storage import ManifestFilesMixin
from pipeline.storage import PipelineMixin

from django.conf import settings


class PatchedS3Boto3Storage(S3Boto3Storage):
    def _save_content(self, obj, content, parameters):
        """
        We create a clone of the content file as when this is passed to boto3
        it wrongly closes the file upon upload where as the storage backend
        expects it to still be open
        """
        # Seek our content back to the start
        content.seek(0, os.SEEK_SET)

        # Create a temporary file that will write to disk after a specified
        # size
        content_autoclose = SpooledTemporaryFile()

        # Write our original content into our copy that will be closed by boto3
        content_autoclose.write(content.read())
        # Upload the object which will auto close the content_autoclose
        # instance
        super()._save_content(obj, content_autoclose, parameters)

        # Cleanup if this is fixed upstream our duplicate should always close
        if not content_autoclose.closed:
            content_autoclose.close()


class StaticStorage(PipelineMixin, ManifestFilesMixin, PatchedS3Boto3Storage):
    """
    Store static files on S3 at STATICFILES_LOCATION, post-process with pipeline
    and then create manifest files for them.
    """

    location = settings.STATICFILES_LOCATION


class MediaStorage(PatchedS3Boto3Storage):
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
