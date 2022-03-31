from unittest import skipIf

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase

from candidates.tests.uk_examples import UK2015ExamplesMixin
from official_documents.models import OfficialDocument
from official_documents.tests.paths import (
    EXAMPLE_DOCX_FILENAME,
    EXAMPLE_HTML_FILENAME,
)
from moderation_queue.tests.paths import EXAMPLE_IMAGE_FILENAME
from ynr.apps.sopn_parsing.helpers.convert_pdf import PandocConversionError
from sopn_parsing.helpers.convert_pdf import convert_sopn_to_pdf
from sopn_parsing.tests import should_skip_conversion_tests


@skipIf(
    should_skip_conversion_tests(), "Required conversion libs not installed"
)
class TestSOPNHelpers(UK2015ExamplesMixin, TestCase):

    example_docx_filename = EXAMPLE_DOCX_FILENAME
    example_html_filename = EXAMPLE_HTML_FILENAME
    example_image_filename = EXAMPLE_IMAGE_FILENAME

    def test_convert_docx_SOPN(self):
        # test converting docx to pdf
        doc = OfficialDocument.objects.create(
            ballot=self.dulwich_post_ballot,
            document_type=OfficialDocument.NOMINATION_PAPER,
            uploaded_file=SimpleUploadedFile(
                "example-file.docx",
                open(self.example_docx_filename, "rb").read(),
            ),
            source_url="example.com",
        )
        convert_sopn_to_pdf(doc.uploaded_file)
        doc.refresh_from_db()
        self.assertTrue(doc.uploaded_file.name.endswith(".pdf"))

    def test_convert_html_SOPN(self):
        # test converting html to pdf
        doc = OfficialDocument.objects.create(
            ballot=self.dulwich_post_ballot,
            document_type=OfficialDocument.NOMINATION_PAPER,
            uploaded_file=SimpleUploadedFile(
                "example-file.html",
                open(self.example_html_filename, "rb").read(),
            ),
            source_url="example.com",
        )
        convert_sopn_to_pdf(doc.uploaded_file)
        self.assertTrue(doc.uploaded_file.name.endswith(".pdf"))

    def test_convert_other_file_to_SOPN(self):
        # when file types are not accepted, raise an error
        with self.assertRaises(PandocConversionError):
            OfficialDocument.objects.create(
                ballot=self.dulwich_post_ballot,
                document_type=OfficialDocument.NOMINATION_PAPER,
                uploaded_file=SimpleUploadedFile(
                    "example-file.jpg",
                    open(self.example_image_filename, "rb").read(),
                ),
                source_url="example.com",
            )
