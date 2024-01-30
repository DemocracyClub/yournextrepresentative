import json
from os.path import dirname, join, realpath
from unittest import skipIf
from unittest.mock import patch

from candidates.models import LoggedAction
from candidates.tests.auth import TestUserMixin
from candidates.tests.factories import (
    ElectionFactory,
    ParliamentaryChamberFactory,
    PartySetFactory,
    PostFactory,
)
from django.urls import reverse
from django_webtest import WebTest
from moderation_queue.tests.paths import EXAMPLE_IMAGE_FILENAME
from official_documents.models import OfficialDocument
from official_documents.tests.paths import (
    EXAMPLE_DOCX_FILENAME,
    EXAMPLE_HTML_FILENAME,
    EXAMPLE_PDF_FILENAME,
)
from sopn_parsing.models import ParsedSOPN
from sopn_parsing.tests import should_skip_conversion_tests
from sopn_parsing.tests.data.welsh_sopn_data import welsh_sopn_data
from webtest import Upload

TEST_MEDIA_ROOT = realpath(
    join(dirname(__file__), "..", "..", "moderation_queue", "tests", "media")
)

# FIXME: it's probably best not to include anything from the
# candidates application in here so that official_documents is
# standalone, so we should at some point replace TestUserMixin with
# creating appropriate users here, and the parts of the tests that
# check whether the upload text appears correctly should be moved to
# the candidates application tests.


class TestModels(TestUserMixin, WebTest):
    example_image_filename = EXAMPLE_IMAGE_FILENAME
    example_docx_filename = EXAMPLE_DOCX_FILENAME
    example_html_filename = EXAMPLE_HTML_FILENAME
    example_pdf_filename = EXAMPLE_PDF_FILENAME

    def setUp(self):
        gb_parties = PartySetFactory.create(slug="gb", name="Great Britain")
        self.election = ElectionFactory.create(
            slug="parl.2015-05-07", name="2015 General Election", current=True
        )
        commons = ParliamentaryChamberFactory.create()
        self.post = PostFactory.create(
            elections=(self.election,),
            organization=commons,
            slug="dulwich-and-west-norwood",
            label="Member of Parliament for Dulwich and West Norwood",
            party_set=gb_parties,
        )
        self.ballot = self.post.ballot_set.get(election=self.election)

    def test_upload_unauthorized(self):
        response = self.app.get(self.ballot.get_absolute_url(), user=self.user)
        csrftoken = self.app.cookies["csrftoken"]
        upload_url = reverse(
            "upload_document_view",
            kwargs={"ballot_paper_id": self.ballot.ballot_paper_id},
        )
        with open(self.example_image_filename, "rb") as f:
            response = self.app.post(
                upload_url,
                params={
                    "csrfmiddlewaretoken": csrftoken,
                    "post_id": self.post.slug,
                    "document_type": OfficialDocument.NOMINATION_PAPER,
                    "source_url": "http://example.org/foo",
                    "": Upload("pilot.jpg", f.read()),
                },
                user=self.user,
                expect_errors=True,
            )
        self.assertEqual(response.status_code, 403)
        self.assertIn(
            "You must be in the member of a particular group in order to view that page",
            response.text,
        )

    def test_upload_authorized(self):
        self.assertFalse(LoggedAction.objects.exists())
        response = self.app.get(
            self.ballot.get_absolute_url(),
            user=self.user_who_can_upload_documents,
        )

        self.assertInHTML("Upload SOPN", response.text)

        response = self.app.get(
            reverse(
                "upload_document_view",
                kwargs={"ballot_paper_id": self.ballot.ballot_paper_id},
            ),
            user=self.user_who_can_upload_documents,
        )
        form = response.forms["document-upload-form"]
        form["source_url"] = "http://example.org/foo"
        with open(self.example_image_filename, "rb") as f:
            form["uploaded_file"] = Upload("pilot.pdf", f.read())

        with patch(
            "official_documents.views.extract_pages_for_ballot"
        ) as extract_pages, patch(
            "official_documents.views.extract_ballot_table"
        ) as extract_tables, patch(
            "official_documents.views.parse_raw_data_for_ballot"
        ) as parse_tables:
            response = form.submit()
            self.assertEqual(response.status_code, 302)
            extract_pages.assert_called_once()
            extract_tables.assert_called_once()
            parse_tables.assert_called_once()

        ods = OfficialDocument.objects.all()
        self.assertEqual(ods.count(), 1)
        od = ods[0]
        self.assertEqual(od.source_url, "http://example.org/foo")
        self.assertEqual(
            od.ballot.ballot_paper_id,
            "parl.dulwich-and-west-norwood.2015-05-07",
        )

        # Test that the document is listed on the all documents page
        url = reverse("unlocked_posts_with_documents")
        response = self.app.get(url)
        self.assertContains(response, "Unlocked posts with nomination papers")

        self.assertContains(
            response, "Member of Parliament for Dulwich and West Norwood"
        )
        qs = LoggedAction.objects.all()
        self.assertEqual(qs.count(), 1)
        self.assertEqual(qs.get().source, "http://example.org/foo")

        response = self.app.get(
            self.ballot.get_sopn_url(), user=self.user_who_can_upload_documents
        )
        self.assertInHTML("Update SOPN", response.text)

    @skipIf(
        should_skip_conversion_tests(), "Required conversion libs not installed"
    )
    def test_docx_upload_form_validation(self):
        self.assertFalse(LoggedAction.objects.exists())
        response = self.app.get(
            self.ballot.get_absolute_url(),
            user=self.user_who_can_upload_documents,
        )

        self.assertInHTML("Upload SOPN", response.text)

        response = self.app.get(
            reverse(
                "upload_document_view",
                kwargs={"ballot_paper_id": self.ballot.ballot_paper_id},
            ),
            user=self.user_who_can_upload_documents,
        )

        form = response.forms["document-upload-form"]
        form["source_url"] = "http://example.org/foo"
        with open(self.example_docx_filename, "rb") as f:
            form["uploaded_file"] = Upload("pilot.docx", f.read())
        response = form.submit()
        self.assertEqual(response.status_code, 302)
        self.assertEqual(OfficialDocument.objects.count(), 1)
        self.assertEqual(response.location, self.ballot.get_sopn_url())

    @skipIf(
        should_skip_conversion_tests(), "Required conversion libs not installed"
    )
    def test_html_upload_form_validation(self):
        self.assertFalse(LoggedAction.objects.exists())
        response = self.app.get(
            self.ballot.get_absolute_url(),
            user=self.user_who_can_upload_documents,
        )

        self.assertInHTML("Upload SOPN", response.text)

        response = self.app.get(
            reverse(
                "upload_document_view",
                kwargs={"ballot_paper_id": self.ballot.ballot_paper_id},
            ),
            user=self.user_who_can_upload_documents,
        )
        form = response.forms["document-upload-form"]
        form["source_url"] = "http://example.org/foo"
        with open(self.example_html_filename, "rb") as f:
            form["uploaded_file"] = Upload("pilot.html", f.read())
        response = form.submit()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(OfficialDocument.objects.count(), 0)
        self.assertInHTML(
            "File extension “html” is not allowed. Allowed extensions are: pdf, docx.",
            response.text,
        )

    def upload_sopn(self, filename=None):
        response = self.app.get(
            reverse(
                "upload_document_view",
                kwargs={"ballot_paper_id": self.ballot.ballot_paper_id},
            ),
            user=self.user_who_can_upload_documents,
        )
        form = response.forms["document-upload-form"]
        form["source_url"] = "http://example.org/foo"
        with open(self.example_pdf_filename, "rb") as f:
            form["uploaded_file"] = Upload(filename, f.read())

        with patch(
            "official_documents.views.extract_pages_for_ballot"
        ) as extract_pages, patch(
            "official_documents.views.extract_ballot_table"
        ) as extract_tables, patch(
            "official_documents.views.parse_raw_data_for_ballot"
        ) as parse_tables:
            response = form.submit()
            self.assertEqual(response.status_code, 302)
            extract_pages.assert_called_once()
            extract_tables.assert_called_once()
            parse_tables.assert_called_once()

    @skipIf(
        should_skip_conversion_tests(), "Required conversion libs not installed"
    )
    def test_jpg_form_validation(self):
        self.assertFalse(LoggedAction.objects.exists())

        response = self.app.get(
            reverse(
                "upload_document_view",
                kwargs={"ballot_paper_id": self.ballot.ballot_paper_id},
            ),
            user=self.user_who_can_upload_documents,
        )
        form = response.forms["document-upload-form"]
        form["source_url"] = "http://example.org/foo"
        with open(self.example_image_filename, "rb") as f:
            form["uploaded_file"] = Upload("pilot.jpg", f.read())
        response = form.submit()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(OfficialDocument.objects.count(), 0)
        self.assertInHTML(
            "File extension “jpg” is not allowed. Allowed extensions are: pdf, docx.",
            response.text,
        )

    def test_filename_updated(self):
        """When a SoPN has already been uploaded, test the filename
        is updated when a new SoPN is uploaded."""

        self.assertFalse(LoggedAction.objects.exists())

        response = self.app.get(
            self.ballot.get_absolute_url(),
            user=self.user_who_can_upload_documents,
        )
        self.assertInHTML("Upload SOPN", response.text)

        self.upload_sopn(filename="initial.pdf")

        ods = OfficialDocument.objects.all()
        self.assertEqual(ods.count(), 1)
        od = ods[0]
        self.assertEqual(od.source_url, "http://example.org/foo")
        self.assertEqual(
            od.uploaded_file.name,
            "official_documents/parl.dulwich-and-west-norwood.2015-05-07/initial.pdf",
        )
        self.assertEqual(
            od.ballot.ballot_paper_id,
            "parl.dulwich-and-west-norwood.2015-05-07",
        )
        dataframe = json.dumps(welsh_sopn_data)
        ParsedSOPN.objects.create(
            sopn=self.ballot.sopn, raw_data=dataframe, status="unparsed"
        )

        # repeat the above with another file and check the filename is updated
        # again
        request = self.app.get(
            self.ballot.get_absolute_url(),
            user=self.user_who_can_upload_documents,
        )

        self.assertInHTML('"SOPN" uploaded.', request.text)
        # at this stage we know the sopn has been uploaded. Now we need to
        # check the filename is updated when a new SoPN is uploaded.

        response = self.app.get(
            reverse(
                "ballot_paper_sopn",
                kwargs={"ballot_id": self.ballot.ballot_paper_id},
            ),
            user=self.user_who_can_upload_documents,
        )

        self.assertInHTML("Update SOPN", response.text)

        self.upload_sopn(filename="replacement.pdf")

        dataframe = json.dumps(
            {
                "0": {
                    "0": "Name of \nCandidate",
                    "1": "BRADBURY \nAndrew John",
                    "2": "COLLINS \nDave",
                    "3": "HARVEY \nPeter John",
                    "4": "JENNER \nMelanie",
                },
                "1": {
                    "0": "Home Address",
                    "1": "10 Fowey Close, \nShoreham by Sea, \nWest Sussex, \nBN43 5HE",
                    "2": "51 Old Fort Road, \nShoreham by Sea, \nBN43 5RL",
                    "3": "76 Harbour Way, \nShoreham by Sea, \nSussex, \nBN43 5HH",
                    "4": "9 Flag Square, \nShoreham by Sea, \nWest Sussex, \nBN43 5RZ",
                },
                "2": {
                    "0": "Description (if \nany)",
                    "1": "Green Party",
                    "2": "Independent",
                    "3": "UK Independence \nParty (UKIP)",
                    "4": "Labour Party",
                },
                "3": {
                    "0": "Name of \nProposer",
                    "1": "Tiffin Susan J",
                    "2": "Loader Jocelyn C",
                    "3": "Hearne James H",
                    "4": "O`Connor Lavinia",
                },
                "4": {
                    "0": "Reason \nwhy no \nlonger \nnominated\n*",
                    "1": "",
                    "2": "",
                    "3": "",
                    "4": "",
                },
            }
        )
        ParsedSOPN.objects.create(
            sopn=self.ballot.sopn, raw_data=dataframe, status="unparsed"
        )

        ods = OfficialDocument.objects.all()
        self.assertEqual(ods.count(), 2)
        od = ods[1]
        self.assertEqual(od.source_url, "http://example.org/foo")
        self.assertEqual(
            od.uploaded_file.name,
            "official_documents/parl.dulwich-and-west-norwood.2015-05-07/replacement.pdf",
        )

        self.assertEqual(
            od.ballot.ballot_paper_id,
            "parl.dulwich-and-west-norwood.2015-05-07",
        )
        response = self.app.get(
            reverse(
                "ballot_paper_sopn",
                kwargs={"ballot_id": self.ballot.ballot_paper_id},
            ),
            user=self.user_who_can_upload_documents,
        )
        self.assertInHTML(
            '<div class="pdf_container" id="sopn-parl.dulwich-and-west-norwood.2015-05-07">',
            response.text,
        )

        # assert the table data contains the new data from the
        # replacement upload and not the initial dataframe
        self.assertIn("10 Fowey Close", response.text)
        self.assertNotIn("1 Example Road", response.text)
