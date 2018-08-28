from compat import BufferDictWriter
import requests
import hashlib

from django.core.management.base import BaseCommand

from official_documents.models import OfficialDocument


class Command(BaseCommand):

    help = "Check the hash of a document against the source"
    fieldnames = [
        "ballot_paper_id",
        "Election name",
        "Area name",
        "Source URL",
        "remote_hash",
        "local_hash",
        "status_code",
        "notes",
    ]

    url_info_cache = {}

    def add_arguments(self, parser):
        parser.add_argument("--election-date", action="store", required=True)

    def handle(self, *args, **options):
        self.out_csv = BufferDictWriter(self.fieldnames)
        self.out_csv.writeheader()

        qs = OfficialDocument.objects.filter(
            election__election_date=options["election_date"]
        )

        for document in qs:
            self.check_doc(document)
        self.stdout.write(self.out_csv.output)

    def get_hash(self, sopn_file):
        md5 = hashlib.md5()
        md5.update(sopn_file)
        return md5.hexdigest()

    def check_doc(self, doc):
        line = {
            "ballot_paper_id": doc.post_election.ballot_paper_id,
            "Election name": doc.post_election.election.name,
            "Area name": doc.post_election.post.label,
            "Source URL": doc.source_url,
        }

        cache = self.url_info_cache.get(doc.source_url, {})
        try:
            if not cache:
                req = requests.get(doc.source_url, stream=True)
                status_code = req.status_code

                cache = {"status_code": status_code}

                if status_code != 200:
                    cache["notes"] = "Remote file missing!"
                else:
                    cache["remote_hash"] = self.get_hash(req.raw.read())
                    cache["local_hash"] = self.get_hash(
                        doc.uploaded_file.file.read()
                    )
                    if not cache["remote_hash"] == cache["local_hash"]:
                        cache["notes"] = "File hash mismatch!"

            line.update(cache)
            self.url_info_cache[doc.source_url] = cache

        except requests.exceptions.RequestException as e:
            cache["notes"] = e

        self.out_csv.writerow(line)
