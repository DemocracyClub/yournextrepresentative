import os
from tempfile import NamedTemporaryFile

import mock
from django.test import TestCase

from candidates.tests.factories import (
    BallotPaperFactory,
    ElectionFactory,
    OrganizationFactory,
    PostFactory,
)
from resultsbot.importers.modgov import ModGovElection, ModGovImporter

KIRKLEES_XML = open(
    os.path.join(
        os.path.dirname(__file__), "data/modgov-local.kirklees.2017-10-26.xml"
    )
).read()


def mock_mod_gov(url):

    return mock.Mock(content=KIRKLEES_XML)


def mock_mapping_path():
    return NamedTemporaryFile(delete=False).name


class KirkleesBatleyEastMixin:
    def populate_kirklees_election_data(self):
        self.kirklees_council = OrganizationFactory(name="Kirklees Council")
        self.kirklees_eletion = ElectionFactory(
            slug="local.kirklees.2017-10-26"
        )
        self.batley_east_ward = PostFactory(
            label="Batley East", organization=self.kirklees_council
        )
        self.batley_east_ballot = BallotPaperFactory(
            ballot_paper_id="local.kirklees.batley-east.2017-10-26",
            post=self.batley_east_ward,
            election=self.kirklees_eletion,
            winner_count=1,
        )

    def setUp(self):
        super().setUp()
        self.populate_kirklees_election_data()


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
            print(candidates)
