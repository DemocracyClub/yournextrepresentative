from django.test import TestCase
from official_documents.extract_pages import (
    clean_matcher_data,
)


class TestPageMatching(TestCase):
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
        self.assertDictEqual(clean_matcher_data(match_data), expected_data)
