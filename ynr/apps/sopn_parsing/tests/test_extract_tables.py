from os.path import dirname, join, abspath
from unittest import skipIf

from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.management import call_command
from django.test import TestCase

from candidates.tests.helpers import TmpMediaRootMixin
from candidates.tests.uk_examples import UK2015ExamplesMixin
from official_documents.models import OfficialDocument
from sopn_parsing.helpers.extract_tables import extract_ballot_table
from sopn_parsing.models import ParsedSOPN
from sopn_parsing.tests import should_skip_pdf_tests


class TestSOPNHelpers(TmpMediaRootMixin, UK2015ExamplesMixin, TestCase):
    def setUp(self):
        example_doc_path = abspath(
            join(
                dirname(__file__),
                "data/parl.dulwich-and-west-norwood.2015-05-07.pdf",
            )
        )

        self.doc = OfficialDocument.objects.create(
            ballot=self.dulwich_post_ballot,
            document_type=OfficialDocument.NOMINATION_PAPER,
            uploaded_file=SimpleUploadedFile(
                "sopn.pdf", open(example_doc_path, "rb").read()
            ),
            source_url="example.com",
            relevant_pages="all",
        )

    @skipIf(should_skip_pdf_tests(), "Required PDF libs not installed")
    def test_extract_tables(self):
        extract_ballot_table(self.dulwich_post_ballot)
        self.assertEqual(
            ParsedSOPN.objects.get().as_pandas.to_dict(),
            {
                "0": {
                    "0": "Name of Candidate",
                    "1": "ALAGARATNAM Rathy",
                    "2": "BARBER James",
                    "3": "HAYES Helen Elizabeth",
                    "4": "KANUMANSA Amadu",
                    "5": "KOTECHA Resham",
                    "6": "LAMBERT Robin Andrew David",
                    "7": "NALLY Steve",
                    "8": "NIX Rashid",
                },
                "1": {
                    "0": "Home Address",
                    "1": "(address in the Mitcham and Morden Constituency)",
                    "2": "33 Champion Hill, London, SE5 8BS",
                    "3": "11 Woodsyre, Sydenham Hill, London, SE26 6SS",
                    "4": "11 Coleridge House, Browning Street, London, SE17 1DG",
                    "5": "(address in the Ruislip, Northwood and Pinner Constituency)",
                    "6": "(address in the Duwlich and West Norwood Constituency)",
                    "7": "(address in the Vauxhall Constituency)",
                    "8": "66 Guinness Court, London, SW3 2PQ",
                },
                "2": {
                    "0": "Description (if any)",
                    "1": "UK Independence Party (UKIP)",
                    "2": "Liberal Democrat",
                    "3": "Labour Party",
                    "4": "All People`s Party",
                    "5": "The Conservative Party Candidate",
                    "6": "Independent",
                    "7": "Trade Unionist and Socialist Coalition",
                    "8": "The Green Party",
                },
                "3": {
                    "0": "Name of Assentors Proposer(+), Seconder(++)",
                    "1": "Coleman Alice M + Potter Keith S ++ Potter Stephanie Smith Bryan L Anderson Beth Lumba Avita Andersen Robert Patel Sajal Stanbury Linda Stanbury James",
                    "2": "Fitchett Keith + Price Jonathan ++ Gardner Brigid Waddington Simon Morland Laura Lester Rachel Pidgeon Caroline Hare David Hanton Alastair Haylett Alexander",
                    "3": "Samuel Gaynelle + Whaley Stephen P ++ Brazell Shadi M De Souza Johnny Alcock Heather Natzler Robert S Pearce Michelle E Pickering Robert Richardson Katherine G Pickard Jane",
                    "4": "King James + King Rosemary ++ King David Davies Yadalieu Sesay Mary Rahman Layla K Rahman Syed A Ahmed Jalaluddin Rahman Tajwar S Rahman Taamid S",
                    "5": "Davis James G + Bradbury David S ++ Badman Susan E Hill-Archer Roderick C Langley Anne C Mitchell Andrew M Virgo Marjorie J Virgo Philip A Chathli Lindsay Broomhead Robert A",
                    "6": "Smith Caitlin + Parks Jesse ++ Connage Kyesha Hendry Perihan Mounty E J Sharif B Scott Wellesley Harriott S A Harriott Clive Ojumu Ibi",
                    "7": "Tullis Andrew C + Mason Joshua H ++ Parkinson Francine M Gait Elizabeth Doolan Samantha Ubiaro Elizabeth Garner Stuart Akinjogbin Dolapo Walker Donna Lang Geoffrey P",
                    "8": "Atwell E G + Rose Lloyd ++ O`Shea C Gomes Jacqueline Wood Thomas Rosenfeld David Conroy Martin Skiadopoulou I Rosenfeld Lawrence Rosenfeld Emily",
                },
                "4": {
                    "0": "Reason why no longer nominated*",
                    "1": "",
                    "2": "",
                    "3": "",
                    "4": "",
                    "5": "",
                    "6": "",
                    "7": "",
                    "8": "",
                },
            },
        )

    @skipIf(should_skip_pdf_tests(), "Required PDF libs not installed")
    def test_extract_command_current(self):
        self.assertEqual(ParsedSOPN.objects.count(), 0)
        call_command("sopn_parsing_extract_tables", current=True)
        self.assertEqual(ParsedSOPN.objects.count(), 1)

    def test_extract_command_current_no_current_elections(self):
        self.election.current = False
        self.election.save()
        self.assertEqual(ParsedSOPN.objects.count(), 0)
        call_command("sopn_parsing_extract_tables", current=True)
        self.assertEqual(ParsedSOPN.objects.count(), 0)
