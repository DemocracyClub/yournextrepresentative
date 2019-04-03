import errno
import re
import hashlib
import magic
import mimetypes
import os
from os.path import dirname, join, exists
import requests

from django.core.management.base import BaseCommand
from django.core.files.storage import DefaultStorage

from official_documents.models import OfficialDocument
from sopn_parsing.tasks import extract_and_parse_tables_for_ballot
from candidates.models import PostExtraElection

from compat import BufferDictReader

allowed_mime_types = {
    b"application/pdf",
    b"application/msword",
    b"application/vnd.openxmlformats-officedocument.wordprocessingml.document",
}

headers = {"User-Agent": "DemocracyClub Candidates"}


def download_file_cached(url):
    url_hash = hashlib.md5(url).hexdigest()
    directory = join(dirname(__file__), ".noms-cache")
    try:
        os.mkdir(directory)
    except OSError as e:
        if e.errno != errno.EEXIST:
            raise
    filename = join(directory, url_hash)

    if exists(filename):
        return filename
    try:
        r = requests.get(url, headers=headers)
    except requests.exceptions.SSLError:
        print("Caught an SSLError, so retrying without certificate validation")
        r = requests.get(url, verify=False)
    except:
        print("Error downloading {}".format(url))
        raise
    with open(filename, "w") as f:
        f.write(r.content)
    return filename


def get_column_header(possible_column_headers, row):
    return [ch for ch in possible_column_headers if ch in row][0]


class Command(BaseCommand):
    help = "Import official documents for posts from a URL to a CSV file"

    def add_arguments(self, parser):
        parser.add_argument("--delete-existing", action="store_true")
        parser.add_argument("url")

    def handle(self, *args, **options):

        csv_url = options["url"]

        mime_type_magic = magic.Magic(mime=True)
        storage = DefaultStorage()

        r = requests.get(csv_url)
        r.encoding = "utf-8"
        reader = BufferDictReader(r.text)
        for row in reader:
            pee = PostExtraElection.objects.get(
                ballot_paper_id=row["ballot_paper_id"]
            )
            document_url = row["Link to PDF"]

            if not document_url:
                # print("No URL for {0}".format(name))
                continue
            existing_documents = OfficialDocument.objects.filter(
                document_type=OfficialDocument.NOMINATION_PAPER,
                post_election=pee,
            )
            if existing_documents.count() > 0:
                if options["delete_existing"]:
                    print("Removing existing documents")
                    existing_documents.delete()
                else:
                    msg = "Skipping {0} since it already had documents for {1}"
                    # print(msg.format(name, election))
                    continue
            try:
                downloaded_filename = download_file_cached(document_url)
            except requests.exceptions.ConnectionError:
                print("Connection failed for {}".format(name))
                print("The URL was:", document_url)
                continue
            except requests.exceptions.MissingSchema:
                # This is probably someone putting notes in the URL
                # column, so ignore:
                print(
                    "Probably not a document URL for {}: {}".format(
                        name, document_url
                    )
                )
                continue
            except:
                continue
            mime_type = mime_type_magic.from_file(downloaded_filename)
            extension = mimetypes.guess_extension(mime_type)
            if mime_type not in allowed_mime_types:
                recovered = False
                # Attempt to get a PDF link form the URL
                ignore_urls = ["drive.google.com"]
                if not any([x in document_url for x in ignore_urls]):
                    try:

                        req = requests.get(
                            document_url, headers=headers, verify=False
                        )
                        if req.status_code == 200:
                            re_sre = r'(http[^"\']+\.pdf)'
                            matches = re.findall(re_sre, req.content)
                            if len(matches) == 1:
                                document_url = matches[0]

                            downloaded_filename = download_file_cached(
                                document_url
                            )
                            mime_type = mime_type_magic.from_file(
                                downloaded_filename
                            )
                            extension = mimetypes.guess_extension(mime_type)
                            if mime_type not in allowed_mime_types:
                                raise ValueError(
                                    "Recovery failed to get a PDF for {}".format(
                                        pee.ballot_paper_id
                                    )
                                )
                            else:
                                recovered = True
                    except Exception as e:
                        print(e)

                else:
                    print(
                        "Ignoring unknown MIME type {} for {}".format(
                            mime_type, pee.ballot_paper_id
                        )
                    )
                if not recovered:
                    continue
            filename = "official_documents/{ballot_paper_id}/statement-of-persons-nominated{extension}".format(
                ballot_paper_id=pee.ballot_paper_id, extension=extension
            )
            with open(downloaded_filename, "rb") as f:
                storage_filename = storage.save(filename, f)

            OfficialDocument.objects.create(
                document_type=OfficialDocument.NOMINATION_PAPER,
                uploaded_file=storage_filename,
                election=pee.election,
                post=pee.post,
                post_election=pee,
                source_url=document_url,
            )
            message = (
                "Successfully added the Statement of Persons Nominated for {0}"
            )
            print(message.format(pee.ballot_paper_id))
            extract_and_parse_tables_for_ballot.delay(pee.ballot_paper_id)
