from django.test import TestCase
from official_documents.extract_pages import (
    clean_matcher_data,
)


class TestPageMatching(TestCase):
    def test_page_matching_out_of_order(self):
        """
        Tatsfield & Titsey is on page 4 of the PDF (3 when 0th indexed).

        This shouldn't get flagged as a continuation page.

        :return:
        """

        match_data = [
            {
                "ballot_paper_id": "local.tandridge.bletchingley-nutfield.2024-05-02",
                "label": "Bletchingley & Nutfield",
                "matched": True,
                "matched_page": "0",
            },
            {
                "ballot_paper_id": "local.tandridge.burstow-horne-outwood.2024-05-02",
                "label": "Burstow, Horne & Outwood",
                "matched": True,
                "matched_page": "1",
            },
            {
                "ballot_paper_id": "local.tandridge.chaldon.2024-05-02",
                "label": "Chaldon",
                "matched": True,
                "matched_page": "2",
            },
            {
                "ballot_paper_id": "local.tandridge.dormansland-felbridge.2024-05-02",
                "label": "Dormansland & Felbridge",
                "matched": True,
                "matched_page": "4",
            },
            {
                "ballot_paper_id": "local.tandridge.godstone.2024-05-02",
                "label": "Godstone",
                "matched": True,
                "matched_page": "5",
            },
            {
                "ballot_paper_id": "local.tandridge.harestone.2024-05-02",
                "label": "Harestone",
                "matched": True,
                "matched_page": "6",
            },
            {
                "ballot_paper_id": "local.tandridge.limpsfield.2024-05-02",
                "label": "Limpsfield",
                "matched": True,
                "matched_page": "7",
            },
            {
                "ballot_paper_id": "local.tandridge.lingfield-crowhurst.2024-05-02",
                "label": "Lingfield & Crowhurst",
                "matched": True,
                "matched_page": "8",
            },
            {
                "ballot_paper_id": "local.tandridge.oxted-north.2024-05-02",
                "label": "Oxted North",
                "matched": True,
                "matched_page": "9",
            },
            {
                "ballot_paper_id": "local.tandridge.oxted-south.2024-05-02",
                "label": "Oxted South",
                "matched": True,
                "matched_page": "10",
            },
            {
                "ballot_paper_id": "local.tandridge.portley-queens-park.2024-05-02",
                "label": "Portley & Queens Park",
                "matched": True,
                "matched_page": "11",
            },
            {
                "ballot_paper_id": "local.tandridge.tatsfield-titsey.2024-05-02",
                "label": "Tatsfield & Titsey",
                "matched": True,
                "matched_page": "3",
            },
            {
                "ballot_paper_id": "local.tandridge.valley.2024-05-02",
                "label": "Valley",
                "matched": True,
                "matched_page": "12",
            },
            {
                "ballot_paper_id": "local.tandridge.warlingham-east-chelsham-farleigh.2024-05-02",
                "label": "Warlingham East & Chelsham & Farleigh",
                "matched": True,
                "matched_page": "13",
            },
            {
                "ballot_paper_id": "local.tandridge.warlingham-west.2024-05-02",
                "label": "Warlingham West",
                "matched": True,
                "matched_page": "14",
            },
            {
                "ballot_paper_id": "local.tandridge.westway.2024-05-02",
                "label": "Westway",
                "matched": True,
                "matched_page": "15",
            },
            {
                "ballot_paper_id": "local.tandridge.whyteleafe.2024-05-02",
                "label": "Whyteleafe",
                "matched": True,
                "matched_page": "16",
            },
            {
                "ballot_paper_id": "local.tandridge.woldingham.2024-05-02",
                "label": "Woldingham",
                "matched": True,
                "matched_page": "17",
            },
        ]

        expected_data = {
            "local.tandridge.bletchingley-nutfield.2024-05-02": [0],
            "local.tandridge.burstow-horne-outwood.2024-05-02": [1],
            "local.tandridge.chaldon.2024-05-02": [2],
            "local.tandridge.tatsfield-titsey.2024-05-02": [3],
            "local.tandridge.dormansland-felbridge.2024-05-02": [4],
            "local.tandridge.godstone.2024-05-02": [5],
            "local.tandridge.harestone.2024-05-02": [6],
            "local.tandridge.limpsfield.2024-05-02": [7],
            "local.tandridge.lingfield-crowhurst.2024-05-02": [8],
            "local.tandridge.oxted-north.2024-05-02": [9],
            "local.tandridge.oxted-south.2024-05-02": [10],
            "local.tandridge.portley-queens-park.2024-05-02": [11],
            "local.tandridge.valley.2024-05-02": [12],
            "local.tandridge.warlingham-east-chelsham-farleigh.2024-05-02": [
                13
            ],
            "local.tandridge.warlingham-west.2024-05-02": [14],
            "local.tandridge.westway.2024-05-02": [15],
            "local.tandridge.whyteleafe.2024-05-02": [16],
            "local.tandridge.woldingham.2024-05-02": [17],
        }

        self.assertDictEqual(clean_matcher_data(match_data), expected_data)

    def test_auto_add_continuation_pages(self):
        """
        local.foo.a.2024-05-02 is continued onto page 2 of the PDF (1 when 0th indexed)

        We should add this page to the list of matched_pages

        """
        match_data = [
            {
                "ballot_paper_id": "local.foo.a.2024-05-02",
                "label": "A",
                "matched": True,
                "matched_page": "0",
            },
            {
                "ballot_paper_id": "local.foo.b.2024-05-02",
                "label": "B",
                "matched": True,
                "matched_page": "2",
            },
            {
                "ballot_paper_id": "local.foo.c.2024-05-02",
                "label": "C",
                "matched": True,
                "matched_page": "3",
            },
        ]

        expected_data = {
            "local.foo.a.2024-05-02": [0, 1],
            "local.foo.b.2024-05-02": [2],
            "local.foo.c.2024-05-02": [3],
        }
        self.assertDictEqual(clean_matcher_data(match_data), expected_data)
