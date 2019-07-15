from os.path import abspath, dirname, join
from unittest import skipIf

from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.management import call_command
from django.test import TestCase

from candidates.tests.uk_examples import UK2015ExamplesMixin
from official_documents.models import OfficialDocument
from sopn_parsing.tests import should_skip_pdf_tests


class TestSOPNHelpers(UK2015ExamplesMixin, TestCase):
    @skipIf(should_skip_pdf_tests(), "Required PDF libs not installed")
    def test_extract_pages_management_command(self):
        example_doc_path = abspath(
            join(
                dirname(__file__),
                "data/parl.dulwich-and-west-norwood.2015-05-07.pdf",
            )
        )

        doc = OfficialDocument.objects.create(
            post_election=self.dulwich_post_ballot,
            document_type=OfficialDocument.NOMINATION_PAPER,
            uploaded_file=SimpleUploadedFile(
                "sopn.pdf", open(example_doc_path, "rb").read()
            ),
            source_url="example.com",
        )
        self.assertEqual(doc.first_page_number, None)
        call_command("sopn_parsing_extract_page_numbers", all_documents=True)
        doc.refresh_from_db()
        self.assertEqual(doc.relevant_pages, "all")
