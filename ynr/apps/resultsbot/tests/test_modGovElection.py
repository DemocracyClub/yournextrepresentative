import os
from decimal import Decimal
from tempfile import NamedTemporaryFile

import mock
from django.test import TestCase
from resultsbot.importers.modgov import ModGovElection, ModGovImporter
from resultsbot.tests.mixins import KirkleesBatleyEastMixin

with open(
    os.path.join(
        os.path.dirname(__file__), "data/modgov-local.kirklees.2017-10-26.xml"
    )
) as f:
    KIRKLEES_XML = f.read()


def mock_mod_gov(*args, **kwargs):
    return mock.Mock(content=KIRKLEES_XML)


def mock_mapping_path():
    return NamedTemporaryFile(delete=False).name


@mock.patch(
    "resultsbot.importers.modgov.requests.get", side_effect=mock_mod_gov
)
class TestModGov(KirkleesBatleyEastMixin, TestCase):
    def test_ModGovElection_class(self, *args):
        mg = ModGovElection(KIRKLEES_XML)
        self.assertEqual(mg.title, "Batley East Ward by-election")
        self.assertEqual(mg.num_candidates, 5)
        self.assertEqual(mg.num_divisions, 1)

    @mock.patch(
        "resultsbot.importers.modgov.SavedMapping._get_path",
        side_effect=mock_mapping_path,
    )
    def test_ModGovImporter_class(self, *args):
        mg_importer = ModGovImporter(
            election_id="local.kirklees.2017-10-26",
            url="https://democracy.kirklees.gov.uk/mgWebService.asmx/GetElectionResults?lElectionId=15",
        )

        mg_importer.get_data()
        for div in mg_importer.divisions():
            candidates = list(mg_importer.candidates(div))
            self.assertEqual(len(candidates), 5)

    def test_extra_ballot_data(self, *args):
        """
        Tests that a division can access spoilt ballots etc.
        """

        mg_importer = ModGovImporter(
            election_id="local.kirklees.2017-10-26",
            url="https://democracy.kirklees.gov.uk/mgWebService.asmx/GetElectionResults?lElectionId=15",
        )

        division = mg_importer.divisions().__next__()
        self.assertEqual(division.spoiled_votes, 8)
        self.assertEqual(division.numballotpapersissued, 3437)
        self.assertEqual(division.turnout_percentage, Decimal("25.88"))
