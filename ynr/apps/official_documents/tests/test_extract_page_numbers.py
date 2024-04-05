from pathlib import Path
from unittest import skipIf

from candidates.models import Ballot
from candidates.tests.uk_examples import UK2015ExamplesMixin
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.management import call_command
from django.test import TestCase
from django.utils.text import slugify
from moderation_queue.tests.paths import EXAMPLE_IMAGE_FILENAME
from official_documents.models import ElectionSOPN
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

        example_doc_path = (
            Path(__file__).parent.parent.parent
            / "sopn_parsing/tests/data/halton-2019-statement-of-persons-nominated.pdf"
        )

        # Create ballots
        posts = {
            "Appleton": "0",
            "Beechwood": "1",
            "Birchfield": "2",
            "Broadheath": "3",
            "Daresbury": "4",
            "Ditton": "5",
            "Farnworth": "6",
            "Grange": "7",
            "Halton Brook": "8",
            "Halton Castle": "9",
            "Halton Lea": "10",
            "Halton View": "11",
            "Heath": "12",
            "Hough Green": "13",
            "Kingsway": "14",
            "Mersey": "15",
            "Norton North": "16",
            "Norton South": "17",
            "Riverside": "18",
        }
        self.local_election.ballot_set.all().delete()
        for post_name in posts:
            post = Post.objects.create(
                label=post_name,
                organization=self.local_council,
                identifier=post_name,
            )
            Ballot.objects.create(
                ballot_paper_id="local.{}.2019-05-02".format(
                    slugify(post_name)
                ),
                post=post,
                election=self.local_election,
            )
        with open(example_doc_path, "rb") as f:
            sopn_file = f.read()
        ElectionSOPN.objects.create(
            election=self.local_election,
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
        example_doc_path = (
            Path(__file__).parent.parent.parent
            / "sopn_parsing/tests/data/local.buckinghamshire.amersham-and-chesham-bois.2021-05-06.pdf"
        )
        posts = {"Chalfont St Peter": "6,7", "Chalfont St Giles": "4,5"}
        self.local_election.ballot_set.all().delete()
        with open(example_doc_path, "rb") as f:
            sopn_file = f.read()
            ElectionSOPN.objects.create(
                election=self.local_election,
                uploaded_file=SimpleUploadedFile("sopn.pdf", sopn_file),
                source_url="example.com",
            )
        for post_name in posts:
            post = Post.objects.create(
                label=post_name,
                organization=self.local_council,
                identifier=post_name,
            )
            Ballot.objects.create(
                ballot_paper_id="local.{}.2019-05-02".format(post_name.lower()),
                post=post,
                election=self.local_election,
            )

        call_command("sopn_parsing_extract_page_numbers")
        for post_name, expected_page in posts.items():
            with self.subTest(msg=post_name):
                ballot = Ballot.objects.get(post__label=post_name)
                self.assertEqual(ballot.sopn.relevant_pages, expected_page)
