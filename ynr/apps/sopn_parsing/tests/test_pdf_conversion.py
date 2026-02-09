from candidates.tests.uk_examples import UK2015ExamplesMixin
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from moderation_queue.tests.paths import EXAMPLE_IMAGE_FILENAME
from official_documents.models import BallotSOPN
from official_documents.tests.paths import (
    EXAMPLE_DOCX_FILENAME,
    EXAMPLE_HTML_FILENAME,
)
from sopn_parsing.helpers.convert_pdf import (
    PandocConversionError,
    convert_docx_to_pdf,
)


class TestSOPNHelpers(UK2015ExamplesMixin, TestCase):
    example_docx_filename = EXAMPLE_DOCX_FILENAME
    example_html_filename = EXAMPLE_HTML_FILENAME
    example_image_filename = EXAMPLE_IMAGE_FILENAME

    def test_convert_docx_SOPN(self):
        # test converting docx to pdf
        with open(self.example_docx_filename, "rb") as f:
            sopn_file = f.read()
        doc = BallotSOPN.objects.create(
            ballot=self.dulwich_post_ballot,
            uploaded_file=SimpleUploadedFile(
                "example-file.docx",
                sopn_file,
            ),
            source_url="example.com",
        )
        new_file = convert_docx_to_pdf(doc.uploaded_file)
        self.assertTrue(new_file.name.endswith(".pdf"))

    def test_convert_html_SOPN(self):
        # test converting html to pdf
        with open(self.example_html_filename, "rb") as f:
            sopn_file = f.read()
        doc = BallotSOPN.objects.create(
            ballot=self.dulwich_post_ballot,
            uploaded_file=SimpleUploadedFile(
                "example-file.html",
                sopn_file,
            ),
            source_url="example.com",
        )
        with self.assertRaises(PandocConversionError):
            convert_docx_to_pdf(doc.uploaded_file)

    def test_convert_other_file_to_SOPN(self):
        # when file types are not accepted, raise an error
        with open(self.example_image_filename, "rb") as f:
            sopn_file = f.read()
        doc = BallotSOPN.objects.create(
            ballot=self.dulwich_post_ballot,
            uploaded_file=SimpleUploadedFile(
                "example-file.jpg",
                sopn_file,
            ),
            source_url="example.com",
        )
        with self.assertRaises(PandocConversionError):
            convert_docx_to_pdf(doc.uploaded_file)
