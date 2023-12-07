from os.path import abspath, dirname, join
from unittest import skipIf
from unittest.mock import patch

from candidates.models import Ballot
from candidates.tests.uk_examples import UK2015ExamplesMixin
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.management import call_command
from django.test import TestCase
from moderation_queue.tests.paths import EXAMPLE_IMAGE_FILENAME
from official_documents.models import OfficialDocument
from official_documents.tests.paths import (
    EXAMPLE_DOCX_FILENAME,
    EXAMPLE_HTML_FILENAME,
)
from popolo.models import Post
from sopn_parsing.tests import should_skip_pdf_tests


@skipIf(should_skip_pdf_tests(), "Required PDF libs not installed")
class TestSOPNHelpers(UK2015ExamplesMixin, TestCase):
    example_docx_filename = EXAMPLE_DOCX_FILENAME
    example_html_filename = EXAMPLE_HTML_FILENAME
    example_image_filename = EXAMPLE_IMAGE_FILENAME

    def test_extract_pages_management_command(self):
        example_doc_path = abspath(
            join(
                dirname(__file__),
                "data/parl.dulwich-and-west-norwood.2015-05-07.pdf",
            )
        )
        with open(example_doc_path, "rb") as f:
            sopn_file = f.read()
        doc = OfficialDocument.objects.create(
            ballot=self.dulwich_post_ballot,
            document_type=OfficialDocument.NOMINATION_PAPER,
            uploaded_file=SimpleUploadedFile("sopn.pdf", sopn_file),
            source_url="example.com",
        )
        self.assertEqual(doc.first_page_number, None)
        with patch(
            "sopn_parsing.management.commands.sopn_parsing_extract_page_numbers.extract_pages_for_ballot"
        ) as mock_extract_pages_for_ballot:
            call_command("sopn_parsing_extract_page_numbers")
            mock_extract_pages_for_ballot.assert_called_with(doc.ballot)

    def test_multi_page_sopn_correct_ward_assigning(self):
        """
        In the case where:

        1. More than one ward is covered in a SOPN
        2. The wards covered contains two wards, where one name is a subset of
           the other

        We could end up with a false positive. This is known as the
        "Heath/Broadheath" problem, and was reported here:

        https://github.com/DemocracyClub/yournextrepresentative/issues/911

        This test ensures the correct pages are matched.

        """
        example_doc_path = abspath(
            join(
                dirname(__file__),
                "data/halton-2019-statement-of-persons-nominated.pdf",
            )
        )

        # Create ballots
        posts = {
            "Appleton": "1",
            "Beechwood": "2",
            "Birchfield": "3",
            "Broadheath": "4",
            "Daresbury": "5",
            "Ditton": "6",
            "Farnworth": "7",
            "Grange": "8",
            "Halton Brook": "9",
            "Halton Castle": "10",
            "Halton Lea": "11",
            "Halton View": "12",
            "Heath": "13",
            "Hough Green": "14",
            "Kingsway": "15",
            "Mersey": "16",
            "Norton North": "17",
            "Norton South": "18",
            "Riverside": "19",
        }
        for post_name in posts:
            post = Post.objects.create(
                label=post_name,
                organization=self.local_council,
                identifier=post_name,
            )
            ballot = Ballot.objects.create(
                ballot_paper_id="local.{}.2019-05-02".format(post_name.lower()),
                post=post,
                election=self.local_election,
            )
            with open(example_doc_path, "rb") as f:
                sopn_file = f.read()
            OfficialDocument.objects.create(
                ballot=ballot,
                document_type=OfficialDocument.NOMINATION_PAPER,
                uploaded_file=SimpleUploadedFile("sopn.pdf", sopn_file),
                source_url="example.com",
            )

        call_command("sopn_parsing_extract_page_numbers")
        for post_name, expected_page in posts.items():
            with self.subTest(msg=post_name):
                ballot = Ballot.objects.get(post__label=post_name)
                self.assertEqual(ballot.sopn.relevant_pages, expected_page)

    def test_post_names_same_length(self):
        """
        Test an edge case where SOPN covers wards with similar post names and
        have the same length
        """
        example_doc_path = abspath(
            join(
                dirname(__file__),
                "data/local.buckinghamshire.amersham-and-chesham-bois.2021-05-06.pdf",
            )
        )
        posts = {"Chalfont St Peter": "7,8", "Chalfont St Giles": "5,6"}
        for post_name in posts:
            post = Post.objects.create(
                label=post_name,
                organization=self.local_council,
                identifier=post_name,
            )
            ballot = Ballot.objects.create(
                ballot_paper_id="local.{}.2019-05-02".format(post_name.lower()),
                post=post,
                election=self.local_election,
            )
            with open(example_doc_path, "rb") as f:
                sopn_file = f.read()
            OfficialDocument.objects.create(
                ballot=ballot,
                document_type=OfficialDocument.NOMINATION_PAPER,
                uploaded_file=SimpleUploadedFile("sopn.pdf", sopn_file),
                source_url="example.com",
            )

        call_command("sopn_parsing_extract_page_numbers")
        for post_name, expected_page in posts.items():
            with self.subTest(msg=post_name):
                ballot = Ballot.objects.get(post__label=post_name)
                self.assertEqual(ballot.sopn.relevant_pages, expected_page)
