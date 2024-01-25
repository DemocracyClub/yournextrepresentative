import requests
from candidates.models import Ballot
from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand
from elections.models import Election
from official_documents.models import OfficialDocument


class Command(BaseCommand):
    """This command uses the ballots endpoint to loop over each
    ballot and store each sopn pdf (uploaded_file) locally"""

    def add_arguments(self, parser):
        parser.add_argument(
            "--date",
            "-d",
            action="store",
            help="Election date in ISO format, defaults to 2021-05-06",
            default="2021-05-06",
            type=str,
        )
        parser.add_argument(
            "--site_url",
            "-u",
            action="store",
            help="URL of site to download from",
            default="https://candidates.democracyclub.org.uk/",
            type=str,
        )
        parser.add_argument(
            "--election-count",
            "-c",
            action="store",
            help="URL of site to download from",
            default=50,
            type=int,
        )
        parser.add_argument(
            "--election-slugs", "-s", action="store", required=False
        )

    def handle(self, *args, **options):
        site_url = options.get("site_url")
        election_date = options.get("date")
        election_count = options.get("election_count")

        if options["election_slugs"]:
            election_slugs = options["election_slugs"].split(",")
        else:
            election_slugs = Election.objects.filter(
                election_date=election_date
            ).values_list("slug", flat=True)[:election_count]

        for slug in election_slugs:
            url = f"{site_url}api/next/ballots/?has_sopn=1&page_size=200&election_id={slug}"
            self.create_official_documents(url=url)

    def create_official_documents(self, url):
        data = requests.get(url=url).json()
        try:
            next_page = data["next"]
        except KeyError:
            next_page = None
        if "results" in data:
            for ballot_data in data["results"]:
                ballot = Ballot.objects.get(
                    ballot_paper_id=ballot_data["ballot_paper_id"]
                )
                sopn_data = ballot_data["sopn"]

                # if we already have the SOPN no need to recreate
                if ballot.officialdocument_set.filter(
                    source_url=sopn_data["source_url"]
                ).exists():
                    self.stdout.write(
                        f"SOPN already exists for {ballot.ballot_paper_id}"
                    )
                    continue

                # check if we already have an OfficialDocument with this source
                # downloaded
                official_document = OfficialDocument.objects.filter(
                    source_url=sopn_data["source_url"]
                ).first()
                if official_document:
                    # if so we dont need to redownload the file, we can create a new
                    # object for this ballot with the same file
                    self.stdout.write(
                        f"Found SOPN for source {sopn_data['source_url']}"
                    )
                    OfficialDocument.objects.create(
                        ballot=ballot,
                        source_url=sopn_data["source_url"],
                        uploaded_file=official_document.uploaded_file,
                        document_type=OfficialDocument.NOMINATION_PAPER,
                    )
                    continue

                # otherwise we dont have this file stored already, so download it as
                # part of creating the OfficialDocument
                self.stdout.write(
                    f"Downloading SOPN from {sopn_data['uploaded_file']}"
                )
                file_response = requests.get(sopn_data["uploaded_file"])
                file_object = ContentFile(content=file_response.content)
                official_document = OfficialDocument(
                    ballot=ballot,
                    source_url=sopn_data["source_url"],
                    document_type=OfficialDocument.NOMINATION_PAPER,
                )
                file_extension = sopn_data["uploaded_file"].split(".")[-1]
                filename = f"{ballot.ballot_paper_id}.{file_extension}"
                official_document.uploaded_file.save(
                    name=filename, content=file_object
                )
        else:
            self.stdout.write("No results found")

        # this should only be the case where the election object has > 200
        # ballots e.g. parliamentary elections
        if next_page:
            return self.create_official_documents(url=next_page)
        return None
