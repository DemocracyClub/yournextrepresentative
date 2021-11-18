import requests
import os
from django.core.management import call_command
from sopn_parsing.helpers.command_helpers import BaseSOPNParsingCommand
from django.core.files.base import ContentFile

from candidates.models import Ballot
from official_documents.models import OfficialDocument


class Command(BaseSOPNParsingCommand):
    """This command uses the ballots endpoint to loop over each
    ballot and store each sopn pdf (uploaded_file) locally"""

    def handle(self, *args, **options):
        response = requests.get(
            "https://candidates.democracyclub.org.uk/api/next/ballots?has_sopn=1"
        )
        data = response.json()

        self.create_official_documents(ballots=data["results"])
        # pdf_files = self.get_pdfs(data)

        # self.save_pdfs(pdf_files)
        # # TO DO pass the saved pdfs to the management commands below
        # call_command("sopn_parsing_extract_page_numbers")
        # call_command("sopn_parsing_extract_tables")
        # call_command("sopn_parsing_parse_tables")

    # loop over ballots and extract uploaded_file
    def get_pdfs(self, data):
        pdf_files = []
        for ballot in data["results"]:
            if ballot["sopn"]["uploaded_file"]:
                # TO DO if ballot["sopn"]["uploaded_file"] ends in .docx (or any non .pdf format),
                # convert it to a .pdf
                pdf_files.append(ballot["sopn"]["uploaded_file"])
        return pdf_files

    # store list of pdf files and save them individually/locally
    def save_pdfs(self, pdf_files):
        # loop over each pdf in pdf_files
        for pdf in pdf_files:
            # request the url of the pdf
            response = requests.get(pdf)
            # set the file directory to save the pdfs
            file_dir = os.path.join(
                os.getcwd(), "ynr/apps/sopn_parsing/tests/data"
            )
            # format the file to be saved
            with open(os.path.join(file_dir, pdf.split("/")[-1]), "wb") as file:
                file.write(response.content)
            # sanity check!
            # print(f"Saved {pdf.split('/')[-1]}")

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
