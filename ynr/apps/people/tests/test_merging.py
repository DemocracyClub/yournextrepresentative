from datetime import date, timedelta
from unittest import skip

from candidates.models import LoggedAction
from candidates.models.db import ActionType
from candidates.tests.auth import TestUserMixin
from candidates.tests.factories import PostFactory
from candidates.tests.uk_examples import UK2015ExamplesMixin
from django.contrib.auth import get_user_model
from django.test import RequestFactory
from django_webtest import WebTest
from moderation_queue.tests.paths import EXAMPLE_IMAGE_FILENAME
from people.merging import InvalidMergeError, PersonMerger, UnsafeToDelete
from people.models import GenderGuess, Person, PersonImage
from people.tests.factories import PersonFactory
from popolo.models import Membership
from results.models import ResultEvent
from uk_results.models import CandidateResult, ResultSet


class TestMerging(TestUserMixin, UK2015ExamplesMixin, WebTest):
    def setUp(self):
        self.dest_person = PersonFactory()
        self.source_person = PersonFactory()

    def test_person_merging(self):
        """
        A small interface / smoke test for the PersonMerger class.

        Swap source and dest in the args to ensure dest is always kept
        """

        LoggedAction.objects.create(
            person=self.source_person,
            action_type=ActionType.PERSON_MERGE,
            user=self.user,
        )
        LoggedAction.objects.create(
            person=self.dest_person,
            action_type=ActionType.PERSON_MERGE,
            user=self.user,
        )

        self.assertEqual(Person.objects.count(), 2)
        self.assertEqual(LoggedAction.objects.count(), 2)

        merger = PersonMerger(self.source_person, self.dest_person)
        merger.merge()

        self.assertEqual(Person.objects.count(), 1)
        self.assertEqual(Person.objects.get().pk, self.dest_person.pk)
        # 3 actions, 2 for create, 1 created when the person is deleted
        # No action for the merge as there was no request used
        self.assertEqual(LoggedAction.objects.count(), 3)

    def test_invalid_merge(self):
        other_local_post = PostFactory.create(
            elections=(self.local_election,),
            slug="DIW:E05005005",
            label="Shepway North Ward",
            party_set=self.gb_parties,
            organization=self.local_council,
        )

        self.dest_person.memberships.create(
            ballot=self.local_ballot, party=self.green_party
        )
        self.source_person.memberships.create(
            ballot=other_local_post.ballot_set.get(), party=self.green_party
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
        self.dest_person.memberships.create(
            ballot=self.local_ballot, party=self.green_party
        )
        merger = PersonMerger(self.dest_person, self.source_person)
        with self.assertRaises(UnsafeToDelete):
            merger.safe_delete(self.dest_person)
        self.assertEqual(Person.objects.count(), 2)

    def test_merge_with_results(self):
        self.source_person.memberships.create(
            ballot=self.local_ballot, party=self.green_party, elected=True
        )
        self.dest_person.memberships.create(
            ballot=self.local_ballot, party=self.green_party
        )

        result_set = ResultSet.objects.create(
            ballot=self.local_ballot,
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
        )

        merger = PersonMerger(self.dest_person, self.source_person)
        merger.merge()

        membership = self.dest_person.memberships.get()
        self.assertEqual(membership.result.num_ballots, 3)
        self.assertTrue(membership.elected)

    def test_merge_with_results_on_both_memberships(self):
        self.source_person.memberships.create(
            ballot=self.local_ballot, party=self.green_party, elected=True
        )
        self.dest_person.memberships.create(
            ballot=self.local_ballot, party=self.green_party, elected=True
        )

        result_set = ResultSet.objects.create(
            ballot=self.local_ballot,
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
        )
        CandidateResult.objects.create(
            result_set=result_set,
            membership=self.dest_person.memberships.get(),
            num_ballots=3,
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

    def test_merge_with_previous_party_affiliations(self):
        source_membership = self.source_person.memberships.create(
            ballot=self.senedd_ballot, party=self.ld_party
        )
        source_membership.previous_party_affiliations.add(
            self.conservative_party
        )

        # create the duplication membership without the previous party
        dest_membership = self.dest_person.memberships.create(
            ballot=self.senedd_ballot, party=self.ld_party
        )
        self.assertEqual(dest_membership.previous_party_affiliations.count(), 0)

        # merge and assert that affiliations have been carried over and source
        # membership has been deleted
        merger = PersonMerger(self.dest_person, self.source_person)
        merger.merge()
        self.assertEqual(dest_membership.previous_party_affiliations.count(), 1)
        self.assertEqual(
            dest_membership.previous_party_affiliations.first(),
            self.conservative_party,
        )
        self.assertFalse(
            Membership.objects.filter(pk=source_membership.pk).exists()
        )

    def test_other_names_created(self):
        self.source_person.name = "Joe Bloggs"
        self.source_person.save()

        self.dest_person.name = "Joe Foo Bloggs"
        self.dest_person.save()
        self.assertEqual(self.dest_person.other_names.count(), 0)

        merger = PersonMerger(self.dest_person, self.source_person)
        merger.merge()
        self.assertEqual(self.dest_person.other_names.count(), 1)
        self.assertEqual(
            self.dest_person.other_names.first().name, "Joe Foo Bloggs"
        )

    def test_other_names_not_duplicated(self):
        self.source_person.name = "Joe Bloggs"
        self.source_person.save()
        self.source_person.other_names.create(name="nom de plume")

        self.dest_person.name = "Joe Foo Bloggs"
        self.dest_person.other_names.create(name="nom de plume")
        self.dest_person.save()
        self.assertEqual(self.dest_person.other_names.count(), 1)

        merger = PersonMerger(self.dest_person, self.source_person)
        merger.merge()
        self.assertEqual(self.dest_person.other_names.count(), 2)
        self.assertListEqual(
            list(
                self.dest_person.other_names.order_by("name").values_list(
                    "name", flat=True
                )
            ),
            ["Joe Foo Bloggs", "nom de plume"],
        )

    def test_recorded_merge_data(self):
        self.maxDiff = None
        source_pk = self.source_person.pk
        self.dest_person.name = "Joe Bloggs"
        self.source_person.name = "Joe Foo Bloggs"
        merger = PersonMerger(self.dest_person, self.source_person)
        merger.merge()
        expected_versions = [
            {
                "information_source": "After merging person {}".format(
                    source_pk
                ),
                "version_id": "40e8cf2c0c6e9260",
                "timestamp": "2019-01-28T16:08:53.112792",
                "data": {
                    "biography": "",
                    "birth_date": "",
                    "blog_url": "",
                    "death_date": "",
                    "email": "",
                    "extra_fields": {"favourite_biscuits": ""},
                    "facebook_page_url": "",
                    "facebook_personal_url": "",
                    "gender": "",
                    "homepage_url": "",
                    "honorific_prefix": "",
                    "honorific_suffix": "",
                    "id": str(self.dest_person.pk),
                    "instagram_url": "",
                    "linkedin_url": "",
                    "name": "Joe Bloggs",
                    "other_names": [
                        {
                            "end_date": None,
                            "name": "Joe Foo Bloggs",
                            "note": "",
                            "start_date": None,
                        }
                    ],
                    "party_ppc_page_url": "",
                    "candidacies": {},
                    "twitter_username": "",
                    "mastodon_username": "",
                    "wikidata_id": "",
                    "wikipedia_url": "",
                    "youtube_profile": "",
                },
            }
        ]
        actual = self.dest_person.versions
        self.assertEqual(
            actual[0]["information_source"],
            expected_versions[0]["information_source"],
        )
        self.assertEqual(actual[0]["data"], expected_versions[0]["data"])
        self.assertEqual(len(actual), len(expected_versions))

    def test_dest_person_gets_source_properties(self):
        self.dest_person.birth_date = "1956"
        self.source_person.birth_date = "1945"

        merger = PersonMerger(self.dest_person, self.source_person)
        merger.merge()
        self.assertEqual(self.dest_person.birth_date, "1945")

    def test_dest_person_gets_empty_values_from_source(self):
        self.dest_person.birth_date = None
        self.source_person.birth_date = "1945"

        merger = PersonMerger(self.dest_person, self.source_person)
        merger.merge()
        self.assertEqual(self.dest_person.birth_date, "1945")

    def test_merge_adds_new_image(self):
        PersonImage.objects.create_from_file(
            filename=EXAMPLE_IMAGE_FILENAME,
            new_filename="images/image1.jpg",
            defaults={
                "person": self.dest_person,
                "md5sum": "md5sum",
                "copyright": "example-license",
                "uploading_user": self.user,
                "user_notes": "Here's an image...",
                "source": "Found on the candidate's Flickr feed",
            },
        )

        new_image = PersonImage.objects.create_from_file(
            filename=EXAMPLE_IMAGE_FILENAME,
            new_filename="images/image2.jpg",
            defaults={
                "person": self.source_person,
                "md5sum": "md5sum",
                "copyright": "example-license",
                "uploading_user": self.user,
                "user_notes": "Here's an image...",
                "source": "Found on the candidate's Flickr feed",
            },
        )

        merger = PersonMerger(self.dest_person, self.source_person)
        merger.merge()
        self.dest_person.refresh_from_db()
        self.assertEqual(self.dest_person.image, new_image)

    def test_merge_keeps_old_image(self):
        with self.assertRaises(PersonImage.DoesNotExist):
            self.source_person.image

        old_image = PersonImage.objects.create_from_file(
            filename=EXAMPLE_IMAGE_FILENAME,
            new_filename="images/image1.jpg",
            defaults={
                "person": self.dest_person,
                "md5sum": "md5sum",
                "copyright": "example-license",
                "uploading_user": self.user,
                "user_notes": "Here's an image...",
                "source": "Found on the candidate's Flickr feed",
            },
        )

        merger = PersonMerger(self.dest_person, self.source_person)
        merger.merge()
        self.dest_person.refresh_from_db()
        self.assertEqual(self.dest_person.image, old_image)

    def test_merge_image_when_dest_has_no_image(self):
        with self.assertRaises(PersonImage.DoesNotExist):
            self.dest_person.image

        source_image = PersonImage.objects.create_from_file(
            filename=EXAMPLE_IMAGE_FILENAME,
            new_filename="images/image1.jpg",
            defaults={
                "person": self.source_person,
                "md5sum": "md5sum",
                "copyright": "example-license",
                "uploading_user": self.user,
                "user_notes": "Here's an image...",
                "source": "Found on the candidate's Flickr feed",
            },
        )

        merger = PersonMerger(self.dest_person, self.source_person)
        merger.merge()
        self.dest_person.refresh_from_db()
        self.assertEqual(self.dest_person.image, source_image)

    def test_person_identifier_after_merge(self):
        self.source_person.tmp_person_identifiers.create(
            value_type="email", value="foo@example.com"
        )

        self.assertEqual(self.dest_person.get_email, None)
        self.assertEqual(self.source_person.get_email, "foo@example.com")
        merger = PersonMerger(self.dest_person, self.source_person)
        merger.merge()
        self.assertEqual(self.dest_person.get_email, "foo@example.com")

    def test_person_identifier_keep_dest_id(self):
        self.dest_person.tmp_person_identifiers.create(
            value_type="email", value="old_email@example.com"
        )
        self.source_person.tmp_person_identifiers.create(
            value_type="email", value="new_email@example.com"
        )

        self.assertEqual(self.dest_person.get_email, "old_email@example.com")
        self.assertEqual(self.source_person.get_email, "new_email@example.com")
        merger = PersonMerger(self.dest_person, self.source_person)
        merger.merge()
        self.assertEqual(self.dest_person.get_email, "new_email@example.com")

    def test_merge_queued_images(self):
        self.source_person.queuedimage_set.create()
        self.assertEqual(self.dest_person.queuedimage_set.count(), 0)
        merger = PersonMerger(self.source_person, self.dest_person)
        merger.merge()
        self.assertEqual(self.dest_person.queuedimage_set.count(), 1)

    def test_merge_not_standing(self):
        self.source_person.not_standing.add(self.election)
        self.assertEqual(self.dest_person.not_standing.count(), 0)
        merger = PersonMerger(self.source_person, self.dest_person)
        merger.merge()
        self.assertEqual(self.dest_person.not_standing.count(), 1)

    def test_duplicate_latest_versions_regression(self):
        """
        If there are identical latest versions from the old and new person
        then a "duplicate" version is created, with a "after merging" commit
        message.

        Normally this would get de-duplicated to save filling up the versions
        data, but in the case of a merge we *always* want to keep the merge
        commit, so we can show a proper log message.

        This is a regression test to catch that case.

        https://github.com/DemocracyClub/yournextrepresentative/issues/860

        """

        person_1 = PersonFactory(
            pk=50536,
            versions=[
                {
                    "data": {
                        "birth_date": "",
                        "extra_fields": {"favourite_biscuits": ""},
                        "other_names": [],
                        "facebook_page_url": "",
                        "email": "",
                        "linkedin_url": "",
                        "mastodon_username": "",
                        "party_ppc_page_url": "https://www.wirralconservatives.com/helencameron",
                        "death_date": "",
                        "honorific_suffix": "",
                        "honorific_prefix": "",
                        "name": "Helen Cameron",
                        "twitter_username": "",
                        "id": "50537",
                        "biography": "",
                        "wikipedia_url": "",
                        "candidacies": {
                            "local.wirral.clatterbridge.2019-05-02": {
                                "party": self.conservative_party.ec_id
                            }
                        },
                        "homepage_url": "",
                        "facebook_personal_url": "",
                        "gender": "female",
                    },
                    "information_source": "https://www.wirralconservatives.com/helencameron",
                    "timestamp": "2019-03-28T14:37:30.958127",
                    "version_id": "0036d8081d566648",
                    "username": "harry14",
                }
            ],
        )
        person_2 = PersonFactory(
            pk=50537,
            versions=[
                {
                    "data": {
                        "birth_date": "",
                        "extra_fields": {"favourite_biscuits": ""},
                        "other_names": [],
                        "facebook_page_url": "",
                        "email": "",
                        "linkedin_url": "",
                        "mastodon_username": "",
                        "party_ppc_page_url": "https://www.wirralconservatives.com/helencameron",
                        "death_date": "",
                        "honorific_suffix": "",
                        "honorific_prefix": "",
                        "name": "Helen Cameron",
                        "twitter_username": "",
                        "id": "50536",
                        "biography": "",
                        "wikipedia_url": "",
                        "candidacies": {
                            "local.wirral.clatterbridge.2019-05-02": {
                                "party": self.conservative_party.ec_id
                            }
                        },
                        "homepage_url": "",
                        "facebook_personal_url": "",
                        "gender": "female",
                    },
                    "information_source": "https://www.wirralconservatives.com/helencameron",
                    "timestamp": "2019-03-28T14:37:30.958127",
                    "version_id": "0036d8081d566648",
                    "username": "harry14",
                }
            ],
        )

        merger = PersonMerger(person_1, person_2)
        merger.merge()
        person_1.refresh_from_db()
        # This would raise if the bug existed
        self.assertIsNotNone(person_1.version_diffs)

    @skip("until we can mark as not standing")
    def test_conflicting_standing_in_values_regression(self):
        """
        https://github.com/DemocracyClub/yournextrepresentative/issues/811

        This was both a bug and a problem with the strategy of merging.

        The bug was that is was possible to have party info against an election
        in the not-standing list.

        The problem was when merging two people with a not standing value and a
        membership in the same election, we would keep both objects, leaving
        the database in an inconsistent state.

        The merging logic was changed to keep the membership and discard the
        not-standing status.

        This test checks for a regression of both cases.

        """
        self.local_election.election_date = date.today() + timedelta(days=1)
        self.local_election.save()

        other_local_post = PostFactory.create(
            elections=(self.local_election,),
            slug="LBW:E05000601",
            label="Hoe Street",
            party_set=self.gb_parties,
            organization=self.local_council,
        )
        ballot = other_local_post.ballot_set.get()

        # Create person 1
        response = self.app.get(ballot.get_absolute_url(), user=self.user)
        form = response.forms["new-candidate-form"]
        form["name"] = "Imaginary Candidate"
        form["party_identifier_1"] = self.green_party.ec_id
        form[
            "source"
        ] = "Testing adding a new candidate to a locked constituency"
        response = form.submit().follow()
        person_1 = response.context["person"]

        # Create person 2
        response = self.app.get(ballot.get_absolute_url(), user=self.user)
        form = response.forms["new-candidate-form"]
        form["name"] = "Imaginary Candidate"
        form["party_identifier_1"] = self.green_party.ec_id
        form[
            "source"
        ] = "Testing adding a new candidate to a locked constituency"
        response = form.submit().follow()
        person_2 = response.context["person"]

        # Remove the membership for person 2
        response = self.app.get(
            "/person/{}/update".format(person_2.pk), user=self.user
        )
        form = response.forms["person-details"]
        form["source"] = "Mumsnet"
        form.submit()

        # Merge the two people. What do we expect?
        # We have a standing in and a not-standing record for the same election
        # so we decide to remove the not-standing and keep the membership
        merger = PersonMerger(person_1, person_2)
        merger.merge()
        person_1.refresh_from_db()
        version_data = person_1.versions[0]["data"]
        self.assertEqual(
            version_data["candidacies"],
            {"local.maidstone.LBW:E05000601.2016-05-05": {"party": "PP63"}},
        )

    def test_merge_with_result_event(self):
        ResultEvent.objects.create(
            winner=self.source_person,
            post=self.local_post,
            winner_party=self.green_party,
        )

        merger = PersonMerger(self.dest_person, self.source_person)
        merger.merge()

        result = ResultEvent.objects.get(winner=self.dest_person)
        self.assertEqual(result.winner, self.dest_person)

    def test_merge_person_identifiers_with_duplicate_values(self):
        """
        Regression test for
        https://github.com/DemocracyClub/yournextrepresentative/issues/1007

        If two PersonIdentifiers exist with the same value but different
        value_types then an IntegrityError error was raised
        """

        self.source_person.tmp_person_identifiers.create(
            value_type="facebook_personal", value="example.com/foo"
        )

        self.dest_person.tmp_person_identifiers.create(
            value_type="facebook_page", value="example.com/foo"
        )

        merger = PersonMerger(self.dest_person, self.source_person)
        merger.merge()
        self.assertTrue(
            self.dest_person.tmp_person_identifiers.filter(
                value_type="facebook_page"
            ).exists()
        )
        self.assertFalse(
            self.dest_person.tmp_person_identifiers.filter(
                value_type="facebook_personal"
            ).exists()
        )

    def test_merging_with_gender_guess(self):

        GenderGuess.objects.create(gender="M", person=self.source_person)
        merger = PersonMerger(self.dest_person, self.source_person)
        merger.merge()

    def test_all_fields_have_merge_function(self):
        """
        This is a test that's expected to pass until a new field or relationship
        is added to the `Person` model. At that point, it should fail until a
        merge function has been added.

        """

        supported_fields = set(PersonMerger.SUPPORTED_FIELDS.keys())

        actual_relations = {
            rel.name for rel in self.source_person._meta.related_objects
        }
        actual_fields = {
            field.name for field in self.source_person._meta.get_fields()
        }
        actual_fields.update(actual_relations)
        self.assertSetEqual(supported_fields, actual_fields)

        merge_methods = set(PersonMerger.SUPPORTED_FIELDS.values())
        for method in merge_methods:
            assert hasattr(PersonMerger, method)

    def test_merge_name_and_other_names_uses_shorter_name(self):
        # create original person where full name used
        dest_person = PersonFactory(name="Joe Full Name Bloggs", pk=1357)
        # create newer person with shorter name
        source_person = PersonFactory(name="Joe Bloggs", pk=2357)

        merger = PersonMerger(dest_person, source_person)

        merger.merge_name_and_other_names()

        self.assertEqual(dest_person.name, "Joe Bloggs")
        other_names = dest_person.other_names.values_list("name", flat=True)

        self.assertIn("Joe Full Name Bloggs", other_names)

    def test_person_attrs_to_merge(self):
        """
        Regression test to ensure that 'name' is not included in standard attrs
        to be merged, as it is handled seperately
        """
        merger = PersonMerger(self.dest_person, self.source_person)
        assert "name" not in merger.person_attrs_to_merge

    def test_safe_delete_with_logged_action(self):
        request = RequestFactory()
        request.user = get_user_model().objects.create()
        person_pk = self.source_person.pk
        merger = PersonMerger(self.dest_person, self.source_person, request)
        merger.safe_delete(self.source_person, with_logged_action=True)

        logged_actions = LoggedAction.objects.filter(
            person_pk=person_pk, action_type=ActionType.PERSON_DELETE
        )

        self.assertEqual(logged_actions.count(), 1)
        self.assertEqual(logged_actions.first().user, request.user)
        self.assertFalse(Person.objects.filter(pk=person_pk).exists())
