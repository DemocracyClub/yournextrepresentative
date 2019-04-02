import json
from datetime import date, timedelta

from django_webtest import WebTest

from candidates.tests.uk_examples import UK2015ExamplesMixin
from candidates.tests.auth import TestUserMixin
from candidates.tests.factories import PostFactory
from candidates.models import LoggedAction
from moderation_queue.tests.paths import EXAMPLE_IMAGE_FILENAME
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
        A small interface / smoke test for the PersonMerger class.

        Swap source and dest in the args to ensure dest is always kept
        """

        LoggedAction.objects.create(person=self.source_person, user=self.user)
        LoggedAction.objects.create(person=self.dest_person, user=self.user)

        self.assertEqual(Person.objects.count(), 2)
        self.assertEqual(LoggedAction.objects.count(), 2)

        merger = PersonMerger(self.source_person, self.dest_person)
        merger.merge()

        self.assertEqual(Person.objects.count(), 1)
        self.assertEqual(Person.objects.get().pk, self.dest_person.pk)
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
                    "wikidata_id": "",
                    "honorific_prefix": "",
                    "name": "",
                    "honorific_suffix": "",
                    "gender": "",
                    "birth_date": "",
                    "death_date": "",
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

    def test_dest_person_gets_source_properties(self):
        self.dest_person.birth_date = "1956-01-02"
        self.source_person.birth_date = "1945-01-04"

        merger = PersonMerger(self.dest_person, self.source_person)
        merger.merge()
        self.assertEqual(self.dest_person.birth_date, "1945-01-04")

    def test_dest_person_gets_empty_values_from_source(self):
        self.dest_person.birth_date = None
        self.source_person.birth_date = "1945-01-04"

        merger = PersonMerger(self.dest_person, self.source_person)
        merger.merge()
        self.assertEqual(self.dest_person.birth_date, "1945-01-04")

    def test_merge_maintain_primary_image(self):
        PersonImage.objects.update_or_create_from_file(
            EXAMPLE_IMAGE_FILENAME,
            "images/image1.jpg",
            self.dest_person,
            defaults={
                "md5sum": "md5sum",
                "copyright": "example-license",
                "uploading_user": self.user,
                "user_notes": "Here's an image...",
                "is_primary": True,
                "source": "Found on the candidate's Flickr feed",
            },
        )

        PersonImage.objects.update_or_create_from_file(
            EXAMPLE_IMAGE_FILENAME,
            "images/image2.jpg",
            self.source_person,
            defaults={
                "md5sum": "md5sum",
                "copyright": "example-license",
                "uploading_user": self.user,
                "user_notes": "Here's an image...",
                "is_primary": True,
                "source": "Found on the candidate's Flickr feed",
            },
        )

        self.assertEqual(self.dest_person.images.count(), 1)
        merger = PersonMerger(self.dest_person, self.source_person)
        merger.merge()
        self.assertEqual(self.dest_person.images.count(), 2)
        self.assertEqual(
            self.dest_person.images.filter(is_primary=True).count(), 1
        )

        self.assertTrue(
            self.dest_person.images.get(is_primary=True).image.url.startswith(
                "/media/images/images/image2"
            )
        )

    def test_merge_gets_primary_image(self):
        PersonImage.objects.update_or_create_from_file(
            EXAMPLE_IMAGE_FILENAME,
            "images/image1.jpg",
            self.dest_person,
            defaults={
                "md5sum": "md5sum",
                "copyright": "example-license",
                "uploading_user": self.user,
                "user_notes": "Here's an image...",
                "is_primary": False,
                "source": "Found on the candidate's Flickr feed",
            },
        )

        PersonImage.objects.update_or_create_from_file(
            EXAMPLE_IMAGE_FILENAME,
            "images/image2.jpg",
            self.source_person,
            defaults={
                "md5sum": "md5sum",
                "copyright": "example-license",
                "uploading_user": self.user,
                "user_notes": "Here's an image...",
                "is_primary": True,
                "source": "Found on the candidate's Flickr feed",
            },
        )

        self.assertEqual(self.dest_person.images.count(), 1)
        merger = PersonMerger(self.dest_person, self.source_person)
        merger.merge()
        self.assertEqual(self.dest_person.images.count(), 2)
        self.assertEqual(
            self.dest_person.images.filter(is_primary=True).count(), 1
        )

        self.assertTrue(
            self.dest_person.images.get(is_primary=True).image.url.startswith(
                "/media/images/images/image2"
            )
        )

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
            versions=json.dumps(
                [
                    {
                        "data": {
                            "birth_date": "",
                            "extra_fields": {"favourite_biscuits": ""},
                            "other_names": [],
                            "facebook_page_url": "",
                            "email": "",
                            "linkedin_url": "",
                            "party_ppc_page_url": "https://www.wirralconservatives.com/helencameron",
                            "death_date": "",
                            "honorific_suffix": "",
                            "honorific_prefix": "",
                            "name": "Helen Cameron",
                            "twitter_username": "",
                            "id": "50537",
                            "biography": "",
                            "wikipedia_url": "",
                            "standing_in": {
                                "local.wirral.2019-05-02": {
                                    "name": "Clatterbridge",
                                    "post_id": "MTW:E05000958",
                                }
                            },
                            "homepage_url": "",
                            "party_memberships": {
                                "local.wirral.2019-05-02": {
                                    "name": "Conservative and Unionist Party",
                                    "id": "party:52",
                                }
                            },
                            "facebook_personal_url": "",
                            "gender": "female",
                        },
                        "information_source": "https://www.wirralconservatives.com/helencameron",
                        "timestamp": "2019-03-28T14:37:30.958127",
                        "version_id": "0036d8081d566648",
                        "username": "harry14",
                    }
                ]
            ),
        )
        person_2 = PersonFactory(
            pk=50537,
            versions=json.dumps(
                [
                    {
                        "data": {
                            "birth_date": "",
                            "extra_fields": {"favourite_biscuits": ""},
                            "other_names": [],
                            "facebook_page_url": "",
                            "email": "",
                            "linkedin_url": "",
                            "party_ppc_page_url": "https://www.wirralconservatives.com/helencameron",
                            "death_date": "",
                            "honorific_suffix": "",
                            "honorific_prefix": "",
                            "name": "Helen Cameron",
                            "twitter_username": "",
                            "id": "50536",
                            "biography": "",
                            "wikipedia_url": "",
                            "standing_in": {
                                "local.wirral.2019-05-02": {
                                    "name": "Clatterbridge",
                                    "post_id": "MTW:E05000958",
                                }
                            },
                            "homepage_url": "",
                            "party_memberships": {
                                "local.wirral.2019-05-02": {
                                    "name": "Conservative and Unionist Party",
                                    "id": "party:52",
                                }
                            },
                            "facebook_personal_url": "",
                            "gender": "female",
                        },
                        "information_source": "https://www.wirralconservatives.com/helencameron",
                        "timestamp": "2019-03-28T14:37:30.958127",
                        "version_id": "0036d8081d566648",
                        "username": "harry14",
                    }
                ]
            ),
        )

        merger = PersonMerger(person_1, person_2)
        merger.merge()
        person_1.refresh_from_db()
        # This would raise if the bug existed
        self.assertIsNotNone(person_1.version_diffs)

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
        ballot = other_local_post.postextraelection_set.get()

        # Create person 1
        response = self.app.get(ballot.get_absolute_url(), user=self.user)
        form = response.forms["new-candidate-form"]
        form["name"] = "Imaginary Candidate"
        form[
            "party_GB_{}".format(self.local_election.slug)
        ] = self.green_party.ec_id
        form[
            "constituency_{}".format(self.local_election.slug)
        ] = ballot.post.slug
        form["standing_{}".format(self.local_election.slug)] = "standing"
        form[
            "source"
        ] = "Testing adding a new candidate to a locked constituency"
        response = form.submit()
        person_1 = response.context["object"]

        # Create person 2
        response = self.app.get(ballot.get_absolute_url(), user=self.user)
        form = response.forms["new-candidate-form"]
        form["name"] = "Imaginary Candidate"
        form[
            "party_GB_{}".format(self.local_election.slug)
        ] = self.green_party.ec_id
        form[
            "constituency_{}".format(self.local_election.slug)
        ] = ballot.post.slug
        form["standing_{}".format(self.local_election.slug)] = "standing"
        form[
            "source"
        ] = "Testing adding a new candidate to a locked constituency"
        response = form.submit()
        person_2 = response.context["object"]

        # Remove the membership for person 2
        response = self.app.get(
            "/person/{}/update".format(person_2.pk), user=self.user
        )
        form = response.forms["person-details"]
        form["standing_{}".format(self.local_election.slug)].force_value(
            "not-standing"
        )
        form["source"] = "Mumsnet"
        form.submit()

        # Merge the two people. What do we expect?
        # We have a standing in and a not-standing record for the same election
        # so we decide to remove the not-standing and keep the membership
        merger = PersonMerger(person_1, person_2)
        merger.merge()
        person_1.refresh_from_db()
        version_data = json.loads(person_1.versions)[0]["data"]
        self.assertEqual(
            version_data["standing_in"],
            {
                "local.maidstone.2016-05-05": {
                    "name": "Hoe Street",
                    "post_id": "LBW:E05000601",
                }
            },
        )
        self.assertEqual(
            version_data["party_memberships"],
            {
                "local.maidstone.2016-05-05": {
                    "id": "party:63",
                    "name": "Green Party",
                }
            },
        )
