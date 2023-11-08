from django.test import TestCase
from official_documents.helpers import AWSTextract
from official_documents.models import TextractResult


class TestHelpers(TestCase):
    def setUp(self):
        self.test_sopn = (
            "ynr/apps/sopn_parsing/management/commands/test_sopns/BurySOPN.pdf"
        )
        self.textract_helper = AWSTextract()

    def test_successful_textract_call_creates_textract_result(self):
        self.textract_helper.start_detection(self.test_sopn)
        # assert that the TextractResult object was created on a successful call to Textract
        assert TextractResult.objects.all().count() == 1

    def test_failed_textract_call_raises_exception(self):
        # test that a failed call to Textract raises an exception
        with self.assertRaises(Exception):
            self.textract_helper.start_detection(self.test_sopn)
        # and no TextractResult object is created
        assert TextractResult.objects.all().count() == 0
