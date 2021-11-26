import requests

from django.core.management.base import BaseCommand
from django.core.files.base import ContentFile

from candidates.models import Ballot
from official_documents.models import OfficialDocument


class Command(BaseCommand):
    """This command uses the ballots endpoint to loop over each
    ballot and store each sopn pdf (uploaded_file) locally"""

    def handle(self, *args, **options):
        response = requests.get(
            "https://candidates.democracyclub.org.uk/api/next/ballots?has_sopn=1&page_size=20"
        )
        data = response.json()
        self.create_official_documents(ballots=data["results"])

    def create_official_documents(self, ballots):
        for ballot_data in ballots:
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
