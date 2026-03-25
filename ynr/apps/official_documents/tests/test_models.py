from candidates.tests.factories import (
    ElectionFactory,
    ParliamentaryChamberFactory,
    PostFactory,
)
from django.test import TestCase
from official_documents.models import BallotSOPN


class TestModels(TestCase):
    def setUp(self):
        election = ElectionFactory.create(
            slug="parl.2015-05-07", name="2015 General Election"
        )
        commons = ParliamentaryChamberFactory.create()
        self.post = PostFactory.create(
            elections=(election,),
            organization=commons,
            slug="dulwich-and-west-norwood",
            label="Member of Parliament for Dulwich and West Norwood",
        )
        self.ballot = self.post.ballot_set.get()

    def test_unicode(self):
        doc = BallotSOPN(ballot=self.ballot, source_url="http://example.com/")

        self.assertEqual(
            str(doc),
            "parl.dulwich-and-west-norwood.2015-05-07 (http://example.com/)",
        )


class TestValidateRelevantPages(TestCase):
    def setUp(self):
        election = ElectionFactory.create(
            slug="parl.2015-05-07", name="2015 General Election"
        )
        commons = ParliamentaryChamberFactory.create()
        post = PostFactory.create(
            elections=(election,),
            organization=commons,
            slug="dulwich-and-west-norwood",
            label="Member of Parliament for Dulwich and West Norwood",
        )
        self.ballot = post.ballot_set.get()

    def _make_ballot_sopn(self, relevant_pages):
        sopn = BallotSOPN(ballot=self.ballot, source_url="http://example.com/")
        sopn.relevant_pages = relevant_pages
        return sopn

    def test_valid_all_without_election_sopn(self):
        sopn = self._make_ballot_sopn("all")
        assert sopn.validate_relevant_pages()

    def test_valid_single_page(self):
        sopn = self._make_ballot_sopn("3")
        assert sopn.validate_relevant_pages()

    def test_valid_multiple_pages(self):
        sopn = self._make_ballot_sopn("3,4,5")
        assert sopn.validate_relevant_pages()

    def test_invalid_all_with_election_sopn(self):
        sopn = self._make_ballot_sopn("all")
        sopn.election_sopn_id = 1
        with self.assertRaisesRegex(
            ValueError, "cannot be 'all' when linked to an ElectionSOPN"
        ):
            sopn.validate_relevant_pages()

    def test_invalid(self):
        page_lists = [
            "3,4,6",  # gap
            "5,4,3",  # descending
            "3,5,4",  # out of order
        ]
        for page_list in page_lists:
            with self.subTest(page_list=page_list):
                sopn = self._make_ballot_sopn(page_list)
                with self.assertRaisesRegex(ValueError, "sequential"):
                    sopn.validate_relevant_pages()
