"""
Tests for the code that converts a raw Textract result into a pandas data frame for parsing.
"""
from pathlib import Path

from candidates.tests.uk_examples import UK2015ExamplesMixin
from django.test import TestCase
from official_documents.models import OfficialDocument
from sopn_parsing.models import AWSTextractParsedSOPN


class TestTextractResposeToDataFrame(UK2015ExamplesMixin, TestCase):
    def make_models_from_ballot_id(self, ballot_id) -> AWSTextractParsedSOPN:
        textract_response_path = (
            Path(__file__).parent
            / "data/textract_responses"
            / f"{ballot_id}.json"
        )
        sopn = OfficialDocument.objects.create(ballot=self.dulwich_post_ballot)
        return AWSTextractParsedSOPN.objects.create(
            sopn=sopn, raw_data=textract_response_path.open().read()
        )

    def get_nth_columns(self, df, columns=None):
        if not columns:
            columns = [0, 2]
        return df.iloc[:, columns]

    def get_csv_for_ballot(self, ballot_paper_id, columns=None):
        parsed = self.make_models_from_ballot_id(ballot_paper_id)
        parsed.parse_raw_data()
        df = parsed.as_pandas
        return self.get_nth_columns(df, columns).to_csv()

    def test_simple_ballot(self):
        self.assertEqual(
            self.get_csv_for_ballot(
                "local.cambridgeshire.yaxley-farcet.by.2024-03-21"
            ),
            (
                ",0,2\n"
                "0,Name of Candidate ,Description (if any) \n"
                "1,GULSON Kev ,The Conservative Party Candidate \n"
                "2,HOWELL Sally Ann ,Independent \n"
                "3,ILETT Richard ,Labour Party \n"
                "4,WESTERMAN Ellisa ,The Green Party candidate \n"
                "5,WOOD Andrew Richard ,Liberal Democrat \n"
            ),
        )

    def test_html_ballot(self):
        """
        Saved from HTML, as per
        https://candidates.democracyclub.org.uk/elections/local.mid-devon.upper-yeo-taw.by.2024-03-07/sopn/
        """
        self.assertEqual(
            self.get_csv_for_ballot(
                "local.mid-devon.upper-yeo-taw.by.2024-03-07"
            ),
            (
                ",0,2\n"
                "0,Name of Candidate ,Description (if any) \n"
                "1,HEAL Peter John ,The Conservative Party Candidate \n"
                "2,SCOTLAND Mark ,Green Party \n"
                "3,SHARP Hayden ,Labour Party \n"
                "4,WHITE Alex ,Liberal Democrats \n"
            ),
        )

    def test_scotland_complex_ballot(self):
        """
        Bilingual, as per
        https://candidates.democracyclub.org.uk/elections/local.carmarthenshire.elli.by.2024-03-06/sopn/
        """

        self.assertEqual(
            self.get_csv_for_ballot("local.carmarthenshire.elli.by.2024-03-06"),
            (
                ",0,2\n"
                "0,PERSONAU A ENWEBWYD / PERSONS NOMINATED ,\n"
                "1,1. CYFENW ENWAU ERAILL YN LLAWN 1. SURNAME OTHER NAMES IN FULL ,3. "
                "DISGRIFIAD (Os oes un) 3. DESCRIPTION (if any) \n"
                "2,Beckett Steve ,Plaid Cymru - The Party of Wales \n"
                "3,Burdess Sharon ,Independent \n"
                "4,Erasmus Wayne ,Gwlad Plaid Annibyniaeth Cymru / Gwlad - The Welsh "
                "Independence Party \n"
                "5,Griffiths Justin ,Welsh Liberal Democrats / Democratiaid Rhyddfrydol "
                "Cymru \n"
                "6,Pearce Nick ,Welsh Labour / Llafur Cymru \n"
                "7,Sheehan Hettie ,UKIP \n"
                "8,Williams Richard ,Welsh Conservative Party Candidate / Ymgeisydd Plaid "
                "Geidwadol Cymru \n"
                "9,Williams Stephen ,Independent / Annibynnol \n"
            ),
        )

    def test_multipage_ballot(self):
        """
        Bilingual, as per
        https://candidates.democracyclub.org.uk/elections/mayor.london.2021-05-06/sopn/
        """

        self.assertEqual(
            self.get_csv_for_ballot(
                "mayor.london.2021-05-06", columns=[0, 1, 3]
            ),
            (
                ",0,1,3\n"
                "0,Candidate's Surname ,Other Name(s) ,Description \n"
                "1,BAILEY ,SHAUN ,Conservative Party Candidate \n"
                "2,BALAYEV ,KAM ,Renew \n"
                "3,BERRY ,SIAN ,Green Party \n"
                "4,BINFACE ,COUNT ,Count Binface for Mayor of London \n"
                "5,BROWN ,VALERIE ,The Burning Pink Party \n"
                "6,CORBYN ,PIERS ,Let London Live \n"
                "7,FOSH ,MAX ,Independent \n"
                "8,FOX ,LAURENCE PAUL ,The Reclaim Party \n"
                "9,GAMMONS ,PETER JOHN ,UKIP \n"
                "10,HEWISON ,RICHARD JOHN HOWARD ,Rejoin EU \n"
                '11,HUDSON ,VANESSA HELEN ,"Animal Welfare Party - People, Animals, '
                'Environment "\n'
                "12,Candidate's Surname ,Other Name(s) ,Description \n"
                "13,KELLEHER ,STEVE ,Social Democratic Party \n"
                "14,KHAN ,SADIQ AMAN ,Labour Party \n"
                "15,KURTEN ,DAVID ,Heritage Party \n"
                "16,LONDON ,FARAH ,Independent \n"
                "17,OBUNGE ,NIMS ,Independent \n"
                "18,OMILANA ,NIKO ,Independent \n"
                "19,PORRITT ,LUISA MANON ,Liberal Democrats \n"
                "20,REID ,MANDU KATE ,Vote Women's Equality Party on orange \n"
                "21,ROSE ,BRIAN BENEDICT ,London Real Party \n"
            ),
        )

    def test_name_parsing_ballot(self):
        """
        As per
        https://candidates.democracyclub.org.uk/elections/local.rushmoor.aldershot-park.2023-05-04/sopn/

        Stewart reported that the first letter of each name had a space after it.

        AWS should fix this.
        """

        self.assertEqual(
            self.get_csv_for_ballot(
                "local.rushmoor.aldershot-park.2023-05-04", columns=[0, 1, 3]
            ),
            (
                ",0,1,3\n"
                "0,Candidate name ,Address of candidate2 ,Name of Assentors Proposer(+) "
                "Seconder(++) \n"
                "1,ARMITAGE David Anthony ,(address in Rushmoor) ,Townley Janice A + Townley "
                "Francis A ++ \n"
                "2,MORRELL Sam ,(address in Rushmoor) ,Morrell James S + Breckon Charlotte B "
                "++ \n"
                "3,PORTER Sophie Lee `Ann ,(address in Rushmoor) ,Burton Linda M + Burton "
                "Victoria J ++ \n"
            ),
        )

    def test_multipage_printed_from_html_ballot(self):
        """
        As per
        https://candidates.democracyclub.org.uk/elections/local.dorset.lyme-charmouth.by.2022-04-07/sopn/

        An HTML SOPN that someone printed to PDF. The table spans more than one page
        """

        self.assertEqual(
            self.get_csv_for_ballot(
                "local.dorset.lyme-charmouth.by.2022-04-07", columns=[0, 1, 3]
            ),
            (
                ",0,1,3\n"
                "0,Candidate name ,Address of candidate1 ,Reason why candidate no longer "
                "nominated \n"
                '1,BAWDEN Belinda ,"20 Lym Close, Lyme Regis, DT7 3DE ",\n'
                "2,HART David ,(address in Dorset Council) ,\n"
                '3,REYNOLDS Cheryl Lesley ,"Willowdown, 6 Manor Avenue, Lyme Regis, Dorset, '
                'DT7 3AU ",\n'
                "4,Candidate name ,Address of candidate1 ,Reason why candidate no longer "
                "nominated \n"
                '5,STOCQUELER Vicci ,"9 Pound St, Lyme Regis, DT7 3HZ ",\n'
            ),
        )
