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
                    "0": "Name of \nCandidate",
                    "1": "ALAGARATNAM \nRathy",
                    "2": "BARBER \nJames",
                    "3": "HAYES \nHelen Elizabeth",
                    "4": "KANUMANSA \nAmadu",
                    "5": "KOTECHA \nResham",
                    "6": "LAMBERT \nRobin Andrew \nDavid",
                    "7": "NALLY \nSteve",
                    "8": "NIX \nRashid",
                },
                "1": {
                    "0": "Home \nAddress",
                    "1": "(address in the \nMitcham and Morden \nConstituency)",
                    "2": "33 Champion Hill, \nLondon, SE5 8BS",
                    "3": "11 Woodsyre, \nSydenham Hill, \nLondon, SE26 6SS",
                    "4": "11 Coleridge House, \nBrowning Street, \nLondon, SE17 1DG",
                    "5": "(address in the \nRuislip, Northwood \nand Pinner \nConstituency)",
                    "6": "(address in the \nDuwlich and West \nNorwood \nConstituency)",
                    "7": "(address in the \nVauxhall \nConstituency)",
                    "8": "66 Guinness Court, \nLondon, SW3 2PQ",
                },
                "2": {
                    "0": "Description \n(if any)",
                    "1": "UK Independence \nParty (UKIP)",
                    "2": "Liberal Democrat",
                    "3": "Labour Party",
                    "4": "All People`s Party",
                    "5": "The Conservative \nParty Candidate",
                    "6": "Independent",
                    "7": "Trade Unionist \nand Socialist \nCoalition",
                    "8": "The Green Party",
                },
                "3": {
                    "0": "Name of Assentors \nProposer(+), Seconder(++)",
                    "1": "Coleman Alice M + \n"
                    "Potter Keith S ++ \n"
                    "Potter Stephanie \n"
                    "Smith Bryan L \n"
                    "Anderson Beth \n"
                    "Lumba Avita \n"
                    "Andersen Robert \n"
                    "Patel Sajal \n"
                    "Stanbury Linda \n"
                    "Stanbury James",
                    "2": "Fitchett Keith + \n"
                    "Price Jonathan ++ \n"
                    "Gardner Brigid \n"
                    "Waddington Simon \n"
                    "Morland Laura \n"
                    "Lester Rachel \n"
                    "Pidgeon Caroline \n"
                    "Hare David \n"
                    "Hanton Alastair \n"
                    "Haylett Alexander",
                    "3": "Samuel Gaynelle + \n"
                    "Whaley Stephen P ++ \n"
                    "Brazell Shadi M \n"
                    "De Souza Johnny \n"
                    "Alcock Heather \n"
                    "Natzler Robert S \n"
                    "Pearce Michelle E \n"
                    "Pickering Robert \n"
                    "Richardson Katherine G \n"
                    "Pickard Jane",
                    "4": "King James + \n"
                    "King Rosemary ++ \n"
                    "King David \n"
                    "Davies Yadalieu \n"
                    "Sesay Mary \n"
                    "Rahman Layla K \n"
                    "Rahman Syed A \n"
                    "Ahmed Jalaluddin \n"
                    "Rahman Tajwar S \n"
                    "Rahman Taamid S",
                    "5": "Davis James G + \n"
                    "Bradbury David S ++ \n"
                    "Badman Susan E \n"
                    "Hill-Archer Roderick C \n"
                    "Langley Anne C \n"
                    "Mitchell Andrew M \n"
                    "Virgo Marjorie J \n"
                    "Virgo Philip A \n"
                    "Chathli Lindsay \n"
                    "Broomhead Robert A",
                    "6": "Smith Caitlin + \n"
                    "Parks Jesse ++ \n"
                    "Connage Kyesha \n"
                    "Hendry Perihan \n"
                    "Mounty E J \n"
                    "Sharif B \n"
                    "Scott Wellesley \n"
                    "Harriott S A \n"
                    "Harriott Clive \n"
                    "Ojumu Ibi",
                    "7": "Tullis Andrew C + \n"
                    "Mason Joshua H ++ \n"
                    "Parkinson Francine M \n"
                    "Gait Elizabeth \n"
                    "Doolan Samantha \n"
                    "Ubiaro Elizabeth \n"
                    "Garner Stuart \n"
                    "Akinjogbin Dolapo \n"
                    "Walker Donna \n"
                    "Lang Geoffrey P",
                    "8": "Atwell E G + \n"
                    "Rose Lloyd ++ \n"
                    "O`Shea C \n"
                    "Gomes Jacqueline \n"
                    "Wood Thomas \n"
                    "Rosenfeld David \n"
                    "Conroy Martin \n"
                    "Skiadopoulou I \n"
                    "Rosenfeld Lawrence \n"
                    "Rosenfeld Emily",
                },
                "4": {
                    "0": "Reason why \nno longer \nnominated*",
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
