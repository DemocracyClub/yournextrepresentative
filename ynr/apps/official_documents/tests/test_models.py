from unittest.mock import patch

from candidates.tests.factories import (
    BallotPaperFactory,
    ElectionFactory,
    ParliamentaryChamberFactory,
    PostFactory,
)
from django.core.files.base import ContentFile
from django.test import TestCase
from official_documents.models import (
    BallotSOPN,
    BallotSOPNHistory,
    ElectionSOPN,
    add_ballot_sopns,
)


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


class TestAddBallotSOPNs(TestCase):
    def setUp(self):
        election = ElectionFactory.create(
            slug="parl.2015-05-07", name="2015 General Election"
        )
        commons = ParliamentaryChamberFactory.create()
        self.ballots = [
            BallotPaperFactory(
                election=election,
                post=PostFactory(
                    label=f"Constituency {i}", organization=commons
                ),
                ballot_paper_id=f"ballot{i}",
            )
            for i in range(3)
        ]

    def _sopn(self, ballot, **kwargs):
        kwargs.setdefault("source_url", "http://example.com/")
        return BallotSOPN(
            ballot=ballot,
            uploaded_file=ContentFile(
                b"content", name=f"{ballot.ballot_paper_id}.pdf"
            ),
            **kwargs,
        )

    def test_creates_sopns_and_history(self):
        with patch.object(BallotSOPN, "parse") as parse:
            result = add_ballot_sopns(
                [
                    self._sopn(b, replacement_reason="Because")
                    for b in self.ballots
                ]
            )
        self.assertEqual(len(result), 3)
        self.assertTrue(all(s.pk for s in result))
        self.assertEqual(parse.call_count, 3)
        self.assertEqual(BallotSOPN.objects.count(), 3)
        self.assertEqual(BallotSOPNHistory.objects.count(), 3)
        sopn = BallotSOPN.objects.get(ballot=self.ballots[0])
        history = BallotSOPNHistory.objects.get(ballot=self.ballots[0])
        self.assertEqual(sopn.replacement_reason, "Because")
        self.assertEqual(history.replacement_reason, "Because")
        self.assertEqual(history.source_url, "http://example.com/")
        self.assertEqual(history.relevant_pages, "all")
        self.assertEqual(sopn.uploaded_file.read(), b"content")
        self.assertEqual(history.uploaded_file.read(), b"content")

    def test_none_replacement_reason_stored_as_empty_string(self):
        add_ballot_sopns([self._sopn(self.ballots[0], replacement_reason=None)])
        self.assertEqual(BallotSOPN.objects.get().replacement_reason, "")

    def test_parse_runs_textract_helper(self):
        # mock the whole of TextractSOPNHelper
        # so it won't throw NotUsingAWSException
        # Q_CLUSTER["sync"] is True in testing, so the task runs inline
        with patch(
            "sopn_parsing.helpers.textract_helpers.TextractSOPNHelper"
        ) as helper:
            result = add_ballot_sopns([self._sopn(b) for b in self.ballots[:2]])
        self.assertEqual(
            [call.args[0].pk for call in helper.call_args_list],
            [s.pk for s in result],
        )
        self.assertEqual(helper.return_value.start_detection.call_count, 2)

    def test_replaces_existing_sopn_and_keeps_history(self):
        add_ballot_sopns([self._sopn(self.ballots[0])])
        first_pk = BallotSOPN.objects.get().pk
        add_ballot_sopns(
            [self._sopn(self.ballots[0], source_url="http://example.com/2")],
        )
        sopn = BallotSOPN.objects.get()
        self.assertNotEqual(sopn.pk, first_pk)
        self.assertEqual(sopn.source_url, "http://example.com/2")
        self.assertEqual(BallotSOPNHistory.objects.count(), 2)

    def test_links_election_sopn(self):
        election_sopn = ElectionSOPN.objects.create(
            election=self.ballots[0].election,
            uploaded_file=ContentFile(b"pdf", name="e.pdf"),
        )
        add_ballot_sopns(
            [
                self._sopn(
                    self.ballots[0],
                    election_sopn=election_sopn,
                    relevant_pages="1,2",
                )
            ],
        )
        self.assertEqual(BallotSOPN.objects.get().election_sopn, election_sopn)
        self.assertEqual(BallotSOPNHistory.objects.get().relevant_pages, "1,2")

    def test_validates_everything_before_changing_the_database(self):
        add_ballot_sopns([self._sopn(self.ballots[0])])
        existing = BallotSOPN.objects.get()
        with self.assertRaisesRegex(ValueError, "sequential"):
            add_ballot_sopns(
                [
                    self._sopn(self.ballots[0], relevant_pages="all"),
                    self._sopn(self.ballots[1], relevant_pages="3,5"),
                ],
            )
        self.assertEqual(BallotSOPN.objects.get(), existing)
        self.assertEqual(BallotSOPNHistory.objects.count(), 1)

    def test_is_atomic(self):
        add_ballot_sopns([self._sopn(self.ballots[0])])
        existing = BallotSOPN.objects.get()
        with (
            patch.object(
                BallotSOPN.objects.__class__,
                "bulk_create",
                side_effect=RuntimeError("boom"),
            ),
            self.assertRaises(RuntimeError),
        ):
            add_ballot_sopns([self._sopn(self.ballots[0])])
        self.assertEqual(BallotSOPN.objects.get(), existing)
        self.assertEqual(BallotSOPNHistory.objects.count(), 1)
