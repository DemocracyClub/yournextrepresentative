from os.path import abspath, dirname, join

from candidates.tests.helpers import TmpMediaRootMixin
from candidates.tests.uk_examples import UK2015ExamplesMixin
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.management import call_command
from django.test import TestCase
from django.test.utils import override_settings
from official_documents.models import BallotSOPN
from parties.tests.fixtures import DefaultPartyFixtures


class TestSOPNHelpers(TmpMediaRootMixin, UK2015ExamplesMixin, TestCase):
    def setUp(self):
        example_doc_path = abspath(
            join(
                dirname(__file__),
                "data/parl.dulwich-and-west-norwood.2015-05-07.pdf",
            )
        )
        with open(example_doc_path, "rb") as f:
            sopn_file = f.read()
        self.doc = BallotSOPN.objects.create(
            ballot=self.dulwich_post_ballot,
            uploaded_file=SimpleUploadedFile("sopn.pdf", sopn_file),
            source_url="example.com",
        )


class TestDummySOPNParser(DefaultPartyFixtures, UK2015ExamplesMixin, TestCase):
    @override_settings(USE_DUMMY_PDF_EXTRACTOR=True)
    def test_basic_parsing(self):
        doc = BallotSOPN.objects.create(
            ballot=self.dulwich_post_ballot,
            source_url="example.com",
        )
        self.assertFalse(hasattr(doc, "awstextractparsedsopn"))

        call_command(
            "sopn_parsing_aws_textract",
            ballot=self.dulwich_post_ballot.ballot_paper_id,
            reparse=True,
            blocking=True,
            get_results=True,
            start_analysis=True,
        )
        doc.refresh_from_db()
        # Some smoke tests to see that we've got some data on the model
        self.assertEqual(doc.awstextractparsedsopn.status, "SUCCEEDED")
        self.assertEqual(len(doc.awstextractparsedsopn.as_pandas), 4)
