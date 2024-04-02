import functools
import tempfile
from pathlib import Path

import responses
from candidates.tests.uk_examples import UK2015ExamplesMixin
from django.test import TestCase
from official_documents.management.commands.official_documents_import_sopns import (
    Command,
)
from official_documents.tests.paths import (
    EXAMPLE_DOCX_FILENAME,
    EXAMPLE_PDF_FILENAME,
)


def tempdir(test_func):
    @functools.wraps(test_func)
    def wrapper(*args, **kwargs):
        with tempfile.TemporaryDirectory() as temp_dir:
            return test_func(*args, temp_dir=temp_dir, **kwargs)

    return wrapper


class TestImportSOPNSCommand(UK2015ExamplesMixin, TestCase):
    maxDiff = None

    def test_group_by_source(self):
        sample_csv_data = [
            {
                "Link to PDF": "https://example.com/a",
                "ballot_paper_id": "local.foo.1.2020-01-01",
            },
            {
                "Link to PDF": "https://example.com/a",
                "ballot_paper_id": "local.foo.2.2020-01-01",
            },
            {
                "Link to PDF": "https://example.com/a",
                "ballot_paper_id": "local.foo.3.2020-01-01",
            },
            {
                "Link to PDF": "https://example.com/a",
                "ballot_paper_id": "local.foo.4.2020-01-01",
            },
        ]

        command = Command()
        grouped = command.group_csv_by_source(sample_csv_data)
        self.assertEqual(
            grouped,
            {
                "https://example.com/a": [
                    {
                        "Link to PDF": "https://example.com/a",
                        "ballot_paper_id": "local.foo.1.2020-01-01",
                    },
                    {
                        "Link to PDF": "https://example.com/a",
                        "ballot_paper_id": "local.foo.2.2020-01-01",
                    },
                    {
                        "Link to PDF": "https://example.com/a",
                        "ballot_paper_id": "local.foo.3.2020-01-01",
                    },
                    {
                        "Link to PDF": "https://example.com/a",
                        "ballot_paper_id": "local.foo.4.2020-01-01",
                    },
                ]
            },
        )

    def test_group_data_is_complete_single_ballot(self):
        command = Command()
        ballot_data = [
            {
                "Link to PDF": "https://example.com/a",
                "ballot_paper_id": self.local_ballot.ballot_paper_id,
            },
        ]
        self.assertTrue(command.group_data_is_complete(ballot_data))

        self.assertFalse(command.group_data_is_complete([]))

    def test_group_data_is_not_complete_all_ballots(self):
        command = Command()
        ballot_data = [
            {
                "Link to PDF": "https://example.com/a",
                "ballot_paper_id": self.camberwell_post_ballot.ballot_paper_id,
            },
            {
                "Link to PDF": "https://example.com/a",
                "ballot_paper_id": self.dulwich_post_ballot.ballot_paper_id,
            },
        ]
        self.assertFalse(command.group_data_is_complete(ballot_data))

    def test_group_data_is_complete_all_ballots(self):
        command = Command()
        ballot_data = [
            {
                "Link to PDF": "https://example.com/a",
                "ballot_paper_id": self.camberwell_post_ballot.ballot_paper_id,
            },
            {
                "Link to PDF": "https://example.com/a",
                "ballot_paper_id": self.dulwich_post_ballot.ballot_paper_id,
            },
            {
                "Link to PDF": "https://example.com/a",
                "ballot_paper_id": self.edinburgh_north_post_ballot.ballot_paper_id,
            },
            {
                "Link to PDF": "https://example.com/a",
                "ballot_paper_id": self.edinburgh_east_post_ballot.ballot_paper_id,
            },
        ]
        self.assertTrue(command.group_data_is_complete(ballot_data))

    def test_recover_from_bad_mimetype(self):
        command = Command()
        with open(EXAMPLE_DOCX_FILENAME, "rb") as f:
            example_docx = f.read()

        # We can't deal with Google Drive
        recovered = command.recover_from_bad_mimetype(
            "https://drive.google.com", example_docx
        )
        self.assertIsNone(recovered)

        # This might be an HTML redirect with a link to a PDF
        recovered = command.recover_from_bad_mimetype(
            "https://drive.google.com", example_docx
        )
        self.assertIsNone(recovered)

        recovered = command.recover_from_bad_mimetype(
            "https://example.com/foo.pdf",
            "new url is http://example.com/bar.pdf".encode("utf8"),
        )
        self.assertEqual(recovered, "http://example.com/bar.pdf")

        recovered = command.recover_from_bad_mimetype(
            "https://example.com/foo.pdf", "PDF removed".encode("utf8")
        )
        self.assertIsNone(recovered)

    @tempdir
    @responses.activate
    def test_get_file_path_from_source_url(self, temp_dir):
        temp_dir_path = Path(temp_dir)
        command = Command()
        command.cache_dir_path = temp_dir_path
        source_url = "https://example.com/foo.pdf"

        # Make the file first, ensure it's returned
        with (temp_dir_path / "ff482e275e83289656d1ea202571a1bf").open(
            "wb"
        ) as f:
            with open(EXAMPLE_PDF_FILENAME, "rb") as source_file:
                f.write(source_file.read())
            filename, ext = command.get_file_path_from_source_url(source_url)
        self.assertEqual(filename.name, "ff482e275e83289656d1ea202571a1bf")
        self.assertEqual(ext, ".pdf")

        source_url = "https://example.com/bar.pdf"
        with open(EXAMPLE_PDF_FILENAME, "rb") as f:
            rsp1 = responses.Response(
                method="GET", url=source_url, body=f.read()
            )
            responses.add(rsp1)

        filename, ext = command.get_file_path_from_source_url(source_url)
        self.assertEqual(filename.name, "07ca830c8241830f73170780471b790b")
        self.assertEqual(ext, ".pdf")

    @tempdir
    @responses.activate
    def test_get_file_path_from_source_url_recovery(self, temp_dir):
        temp_dir_path = Path(temp_dir)
        command = Command()
        command.cache_dir_path = temp_dir_path

        source_url = "https://example.com/baz.pdf"
        rsp2 = responses.Response(
            method="GET",
            url=source_url,
            body="https://example.com/bar.pdf".encode(),
        )
        responses.add(rsp2)

        with open(EXAMPLE_PDF_FILENAME, "rb") as f:
            rsp2 = responses.Response(
                method="GET", url="https://example.com/bar.pdf", body=f.read()
            )
            responses.add(rsp2)

        filename, ext = command.get_file_path_from_source_url(source_url)
        self.assertEqual(filename.name, "07ca830c8241830f73170780471b790b")
        self.assertEqual(ext, ".pdf")
