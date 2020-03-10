import os

from django.conf import settings
from django.contrib.staticfiles.storage import ManifestFilesMixin
from django.core.files.storage import FileSystemStorage
from pipeline.storage import PipelineMixin
from storages.backends.s3boto3 import S3Boto3Storage, SpooledTemporaryFile


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


class TestMediaStorage(FileSystemStorage):
    """
    A storage class for use when running tests.

    This class is designed to help tests that interact with media. It will
    set up and clean up a MEDIA_ROOT automatically.
    """

    def url(self, name):
        """
        Override the URL method to return the file path in the temp MEDIA_ROOT.

        This is less than ideal, but is required because of the way Camelot
        tried to open PDF files for parsing (as used in the SOPN parsing app).

        The parser can either be passed a file path or a URL, however when
        using in tests with files that are accessed by a URL, the URL is always
        relative, meaning it starts with a `/`. Camelot assumes this to be
        a file path and attempts to load the file on the local file system.

        To get around this, we set the URL prefix of the file to the value of
        the MEDIA_ROOT.
        """
        return "{}/{}".format(self.base_location, name)
