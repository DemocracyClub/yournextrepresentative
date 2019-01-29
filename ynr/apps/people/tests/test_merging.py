import json

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
        self.dest_person = PersonFactory(pk=1)
        self.source_person = PersonFactory(pk=2)

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

    def test_other_names_created(self):
        self.source_person.name = "Ema Nymnot"
        self.source_person.save()

        self.dest_person.name = "Not My Name"
        self.dest_person.save()
        self.assertEqual(self.dest_person.other_names.count(), 0)

        merger = PersonMerger(self.dest_person, self.source_person)
        merger.merge()
        self.assertEqual(self.dest_person.other_names.count(), 1)
        self.assertEqual(
            self.dest_person.other_names.first().name, "Ema Nymnot"
        )

    def test_other_names_not_duplicated(self):
        self.source_person.name = "Ema Nymnot"
        self.source_person.save()
        self.source_person.other_names.create(name="nom de plume")

        self.dest_person.name = "Not My Name"
        self.dest_person.other_names.create(name="nom de plume")
        self.dest_person.save()
        self.assertEqual(self.dest_person.other_names.count(), 1)

        merger = PersonMerger(self.dest_person, self.source_person)
        merger.merge()
        self.assertEqual(self.dest_person.other_names.count(), 2)
        self.assertListEqual(
            list(self.dest_person.other_names.values_list("name", flat=True)),
            ["Ema Nymnot", "nom de plume"],
        )

    def test_recorded_merge_data(self):
        merger = PersonMerger(self.dest_person, self.source_person)
        merger.merge()
        expected_versions = [
            {
                "information_source": "After merging person 2",
                "version_id": "40e8cf2c0c6e9260",
                "timestamp": "2019-01-28T16:08:53.112792",
                "data": {
                    "id": "1",
                    "email": "",
                    "facebook_page_url": "",
                    "facebook_personal_url": "",
                    "homepage_url": "",
                    "linkedin_url": "",
                    "party_ppc_page_url": "",
                    "twitter_username": "",
                    "wikipedia_url": "",
                    "honorific_prefix": "",
                    "name": "",
                    "honorific_suffix": "",
                    "gender": "",
                    "birth_date": "",
                    "biography": "",
                    "other_names": [],
                    "extra_fields": {"favourite_biscuits": ""},
                    "standing_in": {},
                    "party_memberships": {},
                },
            }
        ]
        actual = json.loads(self.dest_person.versions)
        self.assertEqual(
            actual[0]["information_source"],
            expected_versions[0]["information_source"],
        )
        self.assertEqual(actual[0]["data"], expected_versions[0]["data"])
        self.assertEqual(len(actual), len(expected_versions))

    def test_dest_person_keeps_properties(self):
        self.dest_person.birth_date = "1956-01-02"
        self.source_person.birth_date = "1945-01-04"

        merger = PersonMerger(self.dest_person, self.source_person)
        merger.merge()
        self.assertEqual(self.dest_person.birth_date, "1956-01-02")

    def test_dest_person_gets_empty_values_from_source(self):
        self.dest_person.birth_date = None
        self.source_person.birth_date = "1945-01-04"

        merger = PersonMerger(self.dest_person, self.source_person)
        merger.merge()
        self.assertEqual(self.dest_person.birth_date, "1945-01-04")
