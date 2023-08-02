import os
import zipfile

from django.conf import settings
from django.core.management.base import BaseCommand
from official_documents.models import OfficialDocument


class Command(BaseCommand):
    help = "Create a ZIP file containing all SOPN PDFs"

    def handle(self, *args, **options):
        zip_file_path = os.path.join(settings.MEDIA_ROOT, "all_sopns.zip")
        with zipfile.ZipFile(zip_file_path, "w") as out_zip:
            self.add_files_to_zip(out_zip)

    def add_files_to_zip(self, out_zip):
        for document in OfficialDocument.objects.all():
            doc_name = os.path.join(
                document.election.slug, document.post.slug, str(document.pk)
            )
            doc_name = "{}.{}".format(
                doc_name, document.uploaded_file.path.split(".")[-1]
            )
            out_zip.write(document.uploaded_file.path, doc_name)
