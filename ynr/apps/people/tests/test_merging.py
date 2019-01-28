from django_webtest import WebTest

from candidates.tests.uk_examples import UK2015ExamplesMixin
from candidates.tests.auth import TestUserMixin
from candidates.tests.factories import PostFactory
from candidates.models import LoggedAction
from people.tests.factories import PersonFactory
from uk_results.models import CandidateResult, ResultSet

from people.merging import PersonMerger, InvalidMergeError, UnsafeToDelete
from people.models import Person, PersonImage


class TestMerging(TestUserMixin, UK2015ExamplesMixin, WebTest):
    def setUp(self):
        self.dest_person = PersonFactory()
        self.source_person = PersonFactory()

    def test_person_merging(self):
        """
        A small interface / smoke test for the PersonMerger class
        """

        LoggedAction.objects.create(person=self.source_person, user=self.user)
        LoggedAction.objects.create(person=self.dest_person, user=self.user)

        self.assertEqual(Person.objects.count(), 2)
        self.assertEqual(LoggedAction.objects.count(), 2)

        merger = PersonMerger(self.dest_person, self.source_person)
        merger.merge()

        self.assertEqual(Person.objects.count(), 1)
        self.assertEqual(LoggedAction.objects.count(), 2)

    def test_invalid_merge(self):
        other_local_post = PostFactory.create(
            elections=(self.local_election,),
            slug="DIW:E05005005",
            label="Shepway North Ward",
            party_set=self.gb_parties,
            organization=self.local_council,
        )

        self.dest_person.memberships.create(post_election=self.local_pee)
        self.source_person.memberships.create(
            post_election=other_local_post.postextraelection_set.get()
        )

        self.assertEqual(Person.objects.count(), 2)
        merger = PersonMerger(self.dest_person, self.source_person)
        with self.assertRaises(InvalidMergeError):
            merger.merge()
        # Make sure we still have two people
        self.assertEqual(Person.objects.count(), 2)

    def test_cant_delete_with_related_objects(self):
        """
        It's impossible to test that a model we know about isn't merged, as
        if we knew about a model that wasn't merged we would add a case for it
        in the merging code. However, we can test that `safe_delete` doesn't
        delete objects with related models.
        """
        self.dest_person.memberships.create(post_election=self.local_pee)
        merger = PersonMerger(self.dest_person, self.source_person)
        with self.assertRaises(UnsafeToDelete):
            merger.safe_delete(self.dest_person)
        self.assertEqual(Person.objects.count(), 2)

    def test_merge_with_results(self):
        self.source_person.memberships.create(post_election=self.local_pee)
        self.dest_person.memberships.create(post_election=self.local_pee)

        result_set = ResultSet.objects.create(
            post_election=self.local_pee,
            num_turnout_reported=10000,
            num_spoilt_ballots=30,
            user=self.user,
            ip_address="127.0.0.1",
            source="Example ResultSet for testing",
        )

        CandidateResult.objects.create(
            result_set=result_set,
            membership=self.source_person.memberships.get(),
            num_ballots=3,
            is_winner=True,
        )

        merger = PersonMerger(self.dest_person, self.source_person)
        merger.merge()

        self.assertEqual(
            self.dest_person.memberships.get().result.num_ballots, 3
        )

    def test_merge_with_results_on_both_memberships(self):
        self.source_person.memberships.create(post_election=self.local_pee)
        self.dest_person.memberships.create(post_election=self.local_pee)

        result_set = ResultSet.objects.create(
            post_election=self.local_pee,
            num_turnout_reported=10000,
            num_spoilt_ballots=30,
            user=self.user,
            ip_address="127.0.0.1",
            source="Example ResultSet for testing",
        )

        CandidateResult.objects.create(
            result_set=result_set,
            membership=self.source_person.memberships.get(),
            num_ballots=3,
            is_winner=True,
        )
        CandidateResult.objects.create(
            result_set=result_set,
            membership=self.dest_person.memberships.get(),
            num_ballots=3,
            is_winner=True,
        )

        merger = PersonMerger(self.dest_person, self.source_person)
        with self.assertRaises(InvalidMergeError) as e:
            merger.merge()

        self.assertEqual(
            e.exception.args[0], "Trying to merge two Memberships with results"
        )

        self.assertEqual(
            self.dest_person.memberships.get().result.num_ballots, 3
        )
