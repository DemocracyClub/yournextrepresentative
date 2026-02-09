from os.path import abspath, dirname, join

from candidates.tests.helpers import TmpMediaRootMixin
from candidates.tests.uk_examples import UK2015ExamplesMixin
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from official_documents.models import BallotSOPN


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
