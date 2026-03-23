from django.test import TestCase
from official_documents.views import ElectionSOPNMatchingView


class TestElectionSOPNMatchingView(TestCase):
    def test_validate_payload_valid(self):
        data = {
            "0": "local.foo.a.2024-05-02",
            "1": "CONTINUATION",
            "2": "NOMATCH",
            "3": "local.foo.b.2024-05-02",
            "4": "local.foo.c.2024-05-02",
        }

        view = ElectionSOPNMatchingView()
        assert view.validate_payload(data)

    def test_validate_payload_invalid(self):
        invalid_payloads = [
            # Empty
            {},
            #
            # A page is mapped to None
            # all pages must have a value assigned
            {"0": "local.foo.a.2024-05-02", "1": None},
            #
            # First page is CONTINUATION
            # continuations must follow a ballot page
            {"0": "CONTINUATION", "1": "local.foo.a.2024-05-02"},
            #
            # Page keys are not sequential (gap between 1 and 3)
            {
                "0": "local.foo.a.2024-05-02",
                "1": "local.foo.b.2024-05-02",
                "3": "local.foo.c.2024-05-02",
            },
            #
            # Page keys are not in order
            {
                "1": "local.foo.a.2024-05-02",
                "0": "local.foo.b.2024-05-02",
            },
            #
            # CONTINUATION follows NOMATCH
            # continuation can only follow a ballot page
            {
                "0": "local.foo.a.2024-05-02",
                "1": "NOMATCH",
                "2": "CONTINUATION",
            },
        ]
        view = ElectionSOPNMatchingView()
        for payload in invalid_payloads:
            with self.subTest(payload=payload), self.assertRaises(ValueError):
                view.validate_payload(payload)

    def test_clean_matcher_data(self):
        """
        local.foo.a.2024-05-02 is continued onto
        page 2 of the PDF (1 when 0-indexed)

        We should add this page to the list of matched_pages

        Page 3 (1 when 0-indexed) isn't matched to any ballot
        and should be ignored
        """
        match_data = {
            "0": "local.foo.a.2024-05-02",
            "1": "CONTINUATION",
            "2": "NOMATCH",
            "3": "local.foo.b.2024-05-02",
            "4": "local.foo.c.2024-05-02",
        }

        expected_data = {
            "local.foo.a.2024-05-02": [0, 1],
            "local.foo.b.2024-05-02": [3],
            "local.foo.c.2024-05-02": [4],
        }

        view = ElectionSOPNMatchingView()
        self.assertDictEqual(view.clean_matcher_data(match_data), expected_data)
