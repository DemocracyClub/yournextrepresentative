from os.path import abspath, dirname, join
from unittest import skipIf

from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.management import call_command
from django.test import TestCase

from candidates.models import Ballot
from candidates.tests.uk_examples import UK2015ExamplesMixin
from official_documents.models import OfficialDocument
from popolo.models import Post
from sopn_parsing.tests import should_skip_pdf_tests


@skipIf(should_skip_pdf_tests(), "Required PDF libs not installed")
class TestSOPNHelpers(UK2015ExamplesMixin, TestCase):
    def test_extract_pages_management_command(self):
        example_doc_path = abspath(
            join(
                dirname(__file__),
                "data/parl.dulwich-and-west-norwood.2015-05-07.pdf",
            )
        )

        doc = OfficialDocument.objects.create(
            ballot=self.dulwich_post_ballot,
            document_type=OfficialDocument.NOMINATION_PAPER,
            uploaded_file=SimpleUploadedFile(
                "sopn.pdf", open(example_doc_path, "rb").read()
            ),
            source_url="example.com",
        )
        self.assertEqual(doc.first_page_number, None)
        call_command("sopn_parsing_extract_page_numbers")
        doc.refresh_from_db()
        self.assertEqual(doc.relevant_pages, "all")

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
        posts = {"Heath": "13", "Broadheath": "4"}
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
            OfficialDocument.objects.create(
                ballot=ballot,
                document_type=OfficialDocument.NOMINATION_PAPER,
                uploaded_file=SimpleUploadedFile(
                    "sopn.pdf", open(example_doc_path, "rb").read()
                ),
                source_url="example.com",
                relevant_pages=None,
            )

        call_command("sopn_parsing_extract_page_numbers")
        for post_name, expected_page in posts.items():
            ballot = Ballot.objects.get(post__label=post_name)
            self.assertEqual(ballot.sopn.relevant_pages, expected_page)
