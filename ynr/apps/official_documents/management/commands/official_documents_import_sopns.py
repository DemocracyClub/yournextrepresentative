import csv
import hashlib
import mimetypes
import re
import traceback
from collections import defaultdict
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import magic
import requests
from candidates.models import Ballot
from django.conf import settings
from django.core.files.base import ContentFile
from django.core.files.storage import DefaultStorage
from django.core.management.base import BaseCommand
from elections.models import Election
from official_documents.extract_pages import extract_pages_for_election_sopn
from official_documents.models import (
    ElectionSOPN,
    add_ballot_sopn,
)

allowed_mime_types = {
    "application/pdf",
    "application/msword",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
}

session = requests.session()
headers = {"User-Agent": "DemocracyClub Candidates"}


class Command(BaseCommand):
    help = "Import official documents for posts from a URL to a CSV file"
    delete_existing = False

    def __init__(
        self, stdout=None, stderr=None, no_color=False, force_color=False
    ):
        super().__init__(stdout, stderr, no_color, force_color)
        self.storage = DefaultStorage()
        self.cache_dir_path = Path(settings.PROJECT_ROOT) / ".sopn-cache"
        self.cache_dir_path.mkdir(exist_ok=True, parents=True)
        self.mime_type_magic = magic.Magic(mime=True)
        self.output = csv.writer(self.stdout)

    def add_arguments(self, parser):
        parser.add_argument("--delete-existing", action="store_true")
        parser.add_argument("--reparse", action="store_true")
        parser.add_argument("--full-traceback", action="store_true")
        parser.add_argument("source_url")

    def group_csv_by_source(self, csv_data: csv.DictReader):
        grouped_by_source = defaultdict(list)
        for line in csv_data:
            grouped_by_source[line["Link to PDF"]].append(line)
        return grouped_by_source

    def group_data_is_complete(self, ballot_data: List[Dict]):
        """
        There are two cases where we might consider a ballot to be "complete":

        1. There is a single ballot: this should be a BallotSOPN
        2. There are as many ballots as ballots in the parent election: this is an ElectionSOPN

        Because we import from Google Sheets, it's possible that we import data that's been half populated
        (e.g, someone is adding the same URL to all ballots, but we grab the data before they've finished.)

        In this case we class the ballot as 'incomplete' and move on.

        Of course this could be true in the case of a single ballot (case 1), but we should be able to catch this
        in checks later and manually fix it.

        """
        if not ballot_data:
            # Not sure how we'd end up in this situation, but in any case, it's not complete!
            return False

        if len(ballot_data) == 1:
            # Case 1: single ballot <> source combo, this is a BallotSOPN
            return True

        election = Election.objects.get(
            ballot__ballot_paper_id=ballot_data[0]["ballot_paper_id"]
        )
        if len(ballot_data) == election.ballot_set.count():
            return True

        return False

    def process_group(self, source_url, ballot_data, delete_existing=False):
        if len(ballot_data) == 1:
            ballot = Ballot.objects.get(
                ballot_paper_id=ballot_data[0]["ballot_paper_id"]
            )
            if hasattr(ballot, "sopn") and not self.delete_existing:
                # There's already a SOPN for this ballot, don't replace
                return None
            downloaded_filename, extension = self.get_file_path_from_source_url(
                source_url
            )
            # TODO: convert to PDF here if we need to (e.g docx files)
            upload_filename = f"{ballot.ballot_paper_id}-sopn{extension}"
            with downloaded_filename.open("rb") as sopn_file:
                return add_ballot_sopn(
                    ballot,
                    ContentFile(sopn_file.read(), upload_filename),
                    source_url=source_url,
                )

        # This is an ElectionSOPN
        downloaded_filename, extension = self.get_file_path_from_source_url(
            source_url
        )

        election = Election.objects.get(
            ballot__ballot_paper_id=ballot_data[0]["ballot_paper_id"]
        )
        if hasattr(election, "electionsopn"):
            if delete_existing:
                election.electionsopn.delete()
            else:
                return None
        upload_filename = f"{election.slug}-sopn{extension}"
        with downloaded_filename.open() as sopn_file:
            sopn_upload = ContentFile(sopn_file.read(), upload_filename)
        election_sopn = ElectionSOPN.objects.create(
            election=election,
            source_url=source_url,
            uploaded_file=sopn_upload,
        )
        extract_pages_for_election_sopn(election_sopn)
        for ballot in election_sopn.election.ballot_set.all():
            if hasattr(ballot, "sopn"):
                ballot.sopn.parse()
        return election_sopn

    def get_mimetype_and_extension_from_file_content(self, file_content):
        sopn_mimetype = self.mime_type_magic.from_buffer(file_content)
        return sopn_mimetype, mimetypes.guess_extension(sopn_mimetype)

    def get_file_path_from_source_url(
        self, source_url, fix_mimetype=True
    ) -> Tuple[Path, Optional[str]]:
        """
        This method has to do a few things:

        1. Simply downloading a file from a URL
        2. Caching the downloaded file locally (to speed things up later)
        3. Figuring out some complex downloading dances, e.g Google it hard to download files from Drive
        4. Deal with slow responses and retries

        In general, we want to be able to robustly download files from a source URL.
        """

        url_hash = hashlib.md5(source_url.encode("utf8")).hexdigest()
        filename = self.cache_dir_path / url_hash

        if filename.exists():
            with filename.open("rb") as f:
                (
                    sopn_mimetype,
                    extension,
                ) = self.get_mimetype_and_extension_from_file_content(f.read())
            return filename, extension

        try:
            req = session.get(source_url, headers=headers)
        except requests.exceptions.SSLError:
            req = session.get(source_url, verify=False)
        except requests.exceptions.MissingSchema:
            raise ValueError(f"Not a valid URL {source_url}")
        except requests.exceptions.RequestException:
            raise ValueError(f"Error downloading {source_url}")

        file_content = req.content

        (
            sopn_mimetype,
            extension,
        ) = self.get_mimetype_and_extension_from_file_content(file_content)

        if sopn_mimetype not in allowed_mime_types and fix_mimetype:
            recovered_url = self.recover_from_bad_mimetype(
                source_url, file_content
            )
            if not recovered_url:
                raise ValueError("Can't download PDF")
            # Call this function and return the filename. Don't recursively attempt to recover
            return self.get_file_path_from_source_url(
                recovered_url, fix_mimetype=False
            )

        with filename.open("wb") as f:
            f.write(req.content)

        return filename, extension

    def recover_from_bad_mimetype(self, source_url, file_content):
        """
        If we have a URL with a bad mime-type (e.g, not a file we can process
        there are some cases where the reason is that the server puts in interstitial
        page in place that serves as a redirect.

        We can inspect the content of this page and try to extract the link.

        If we manage that, we can return a new source URL
        """
        ignored_urls = [
            "drive.google.com"  # Google make it really hard to download files
        ]
        # Check if the source URL contains any of the ignored URLs
        if any(item in source_url for item in ignored_urls):
            return None

        re_sre = r'(http[^"\']+\.pdf)'
        matches = re.findall(re_sre, file_content.decode())

        # If there is a single link to a PDF in the response, we assume we can follow it
        if len(matches) == 1:
            return matches[0]

        return None

    def handle(self, *args, **options):  # noqa
        csv_url = options["source_url"]
        self.delete_existing = options["delete_existing"]

        r = requests.get(csv_url)
        r.encoding = "utf-8"
        reader = csv.DictReader(r.text.splitlines())
        grouped = self.group_csv_by_source(reader)
        for url, ballot_data in grouped.items():
            if self.group_data_is_complete(ballot_data):
                try:
                    self.process_group(
                        url,
                        ballot_data,
                        delete_existing=options["delete_existing"],
                    )
                except Exception as ex:
                    if options["full_traceback"]:
                        self.output.writerow([url, traceback.print_exc()])
                    else:
                        self.output.writerow([url, str(ex)])
