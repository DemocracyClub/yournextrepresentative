import copy

from candidates.models import LoggedAction, PersonRedirect
from candidates.models.db import ActionType
from candidates.models.versions import get_versions_parent_map
from candidates.tests.auth import TestUserMixin
from candidates.tests.uk_examples import UK2015ExamplesMixin
from candidates.views.version_data import get_change_metadata
from django.test import TestCase
from freezegun import freeze_time
from people.merging import PersonMerger
from people.models import Person, PersonImage
from people.tests.factories import PersonFactory
from splitting.splitter import InvalidSplitError, PersonSplitter

SPLIT_DAY = "2026-09-28"


def on(day):
    """
    Freeze time during `day`. Not at midnight: isoformat() drops zero
    microseconds, and version_timestamp_key can't parse that.
    """
    return freeze_time(f"{day} 12:00:00.000001")


class SplitSuggestionMixin(TestUserMixin, UK2015ExamplesMixin):
    def record(self, person, when, source="An edit"):
        with on(when):
            person.record_version(
                get_change_metadata(None, source, user=self.user)
            )
            person.save()
        return person.versions[0]["version_id"]

    def make_person(self, name, when, ballots, identifiers=None, **fields):
        with on(when):
            person = PersonFactory(name=name, **fields)
            for ballot, party in ballots:
                person.memberships.create(ballot=ballot, party=party)
            for value_type, value in (identifiers or {}).items():
                person.tmp_person_identifiers.create(
                    value_type=value_type, value=value
                )
        self.record(person, when, source="Created")
        return person

    def merge(self, a, b, when="2026-03-01"):
        with on(when):
            return PersonMerger(a, b).merge()

    def split(self, person, ballot, **kwargs):
        with on(SPLIT_DAY):
            splitter = PersonSplitter(
                person, ballot, user=self.user, suggest=True, **kwargs
            )
            plan = splitter.plan()
            if not plan.is_valid:
                return plan, None
            return plan, splitter.split()


class TestSplitMergedPerson(SplitSuggestionMixin, TestCase):
    def setUp(self):
        super().setUp()
        self.jo = self.make_person(
            "Jo Smith",
            "2026-01-01",
            [(self.dulwich_post_ballot_earlier, self.labour_party)],
        )
        self.joanne = self.make_person(
            "Joanne Smith",
            "2026-02-01",
            [(self.local_ballot, self.green_party)],
            identifiers={"email": "joanne@example.com"},
            gender="female",
        )
        self.joanne_pk = self.joanne.pk
        self.joanne_version = self.joanne.versions[0]["version_id"]
        LoggedAction.objects.create(
            user=self.user,
            person=self.joanne,
            action_type=ActionType.PERSON_CREATE,
            popit_person_new_version=self.joanne_version,
        )

    def test_restores_merged_person_with_old_id(self):
        self.merge(self.jo, self.joanne)
        self.jo.refresh_from_db()
        jo_versions_before = copy.deepcopy(self.jo.versions)
        self.assertEqual(
            self.jo.get_single_identifier_value("email"), "joanne@example.com"
        )

        plan, restored = self.split(self.jo, self.local_ballot)
        self.jo.refresh_from_db()

        self.assertEqual(plan.origin.kind, "merge")
        self.assertEqual(restored.pk, self.joanne_pk)
        self.assertEqual(restored.name, "Joanne Smith")
        self.assertEqual(restored.gender, "female")
        self.assertEqual(
            restored.get_single_identifier_value("email"), "joanne@example.com"
        )
        self.assertEqual(restored.memberships.get().ballot, self.local_ballot)
        self.assertEqual(self.jo.get_single_identifier_value("email"), None)
        self.assertEqual(self.jo.gender, "")
        self.assertFalse(
            PersonRedirect.objects.filter(old_person_id=self.joanne_pk).exists()
        )
        self.assertEqual(
            LoggedAction.objects.get(
                popit_person_new_version=self.joanne_version
            ).person,
            restored,
        )

        # History: the restored person gets theirs back, and the original
        # person's is only added to
        self.assertEqual(restored.versions[0]["data"]["id"], str(restored.pk))
        self.assertIn(
            self.joanne_version, [v["version_id"] for v in restored.versions]
        )
        self.assertEqual(self.jo.versions[1:], jo_versions_before)
        get_versions_parent_map(restored.versions)
        get_versions_parent_map(self.jo.versions)

        # The two people's actions read differently in recent changes
        ballot_id = self.local_ballot.ballot_paper_id
        split = LoggedAction.objects.get(action_type=ActionType.PERSON_SPLIT)
        self.assertEqual(split.person, self.jo)
        self.assertEqual(
            split.source,
            f"After splitting candidacy {ballot_id} to restored person "
            f"{self.joanne_pk}",
        )
        restore = LoggedAction.objects.get(
            person=restored,
            popit_person_new_version=restored.versions[0]["version_id"],
        )
        self.assertEqual(restore.action_type, ActionType.PERSON_CREATE)
        self.assertEqual(
            restore.source,
            f"Restored by splitting candidacy {ballot_id} off person "
            f"{self.jo.pk}",
        )
        self.assertEqual(
            restore.popit_person_new_version, restored.versions[0]["version_id"]
        )

    def test_undoes_name_and_other_names(self):
        self.merge(self.jo, self.joanne)
        self.jo.refresh_from_db()
        self.assertEqual(self.jo.name, "Jo Smith")
        self.assertEqual(
            list(self.jo.other_names.values_list("name", flat=True)),
            ["Joanne Smith"],
        )

        _, restored = self.split(self.jo, self.local_ballot)
        self.jo.refresh_from_db()
        self.assertEqual(self.jo.name, "Jo Smith")
        self.assertFalse(self.jo.other_names.exists())
        self.assertEqual(restored.name, "Joanne Smith")

    def test_recency_cutoff(self):
        # Replace Joanne with someone whose email is old but whose Twitter
        # username is recent
        self.joanne.delete()
        joanne = self.make_person(
            "Joanne Smith",
            "2025-06-01",
            [(self.local_ballot, self.green_party)],
            identifiers={"email": "old@example.com"},
            gender="female",
        )
        joanne.tmp_person_identifiers.create(
            value_type="twitter_username", value="joanne"
        )
        self.record(joanne, "2026-06-01")
        self.merge(self.jo, joanne, when="2026-07-01")
        self.jo.refresh_from_db()

        plan, restored = self.split(self.jo, self.local_ballot, cutoff_days=365)
        email = plan.suggestion_for("email")
        self.assertEqual(email.action, "drop")
        self.assertEqual(plan.suggestion_for("twitter_username").action, "move")
        self.assertEqual(restored.get_single_identifier_value("email"), None)
        self.assertEqual(
            restored.get_single_identifier_value("twitter_username"), "joanne"
        )
        self.assertEqual(restored.gender, "female")

    def test_edit_after_merge_needs_review(self):
        self.merge(self.jo, self.joanne)
        self.jo.refresh_from_db()
        self.jo.tmp_person_identifiers.filter(value_type="email").update(
            value="new@example.com"
        )
        self.record(self.jo, "2026-04-01", source="Found a new email")

        with on(SPLIT_DAY):
            plan = PersonSplitter(
                self.jo, self.local_ballot, suggest=True
            ).plan()
        email = plan.suggestion_for("email")
        self.assertEqual(email.action, "review")
        self.assertIn("Found a new email", email.reason)
        self.assertEqual(email.dest_value, "new@example.com")

        _, restored = self.split(
            self.jo, self.local_ballot, move_fields=["email"]
        )
        self.jo.refresh_from_db()
        self.assertEqual(
            restored.get_single_identifier_value("email"), "new@example.com"
        )
        self.assertEqual(self.jo.get_single_identifier_value("email"), None)

    def test_other_candidacies_move_too(self):
        self.joanne.memberships.create(
            ballot=self.camberwell_post_ballot, party=self.green_party
        )
        self.record(self.joanne, "2026-02-02")
        self.merge(self.jo, self.joanne)
        self.jo.refresh_from_db()

        plan, restored = self.split(self.jo, self.local_ballot)
        self.assertEqual(
            set(
                restored.memberships.values_list(
                    "ballot__ballot_paper_id", flat=True
                )
            ),
            {
                self.local_ballot.ballot_paper_id,
                self.camberwell_post_ballot.ballot_paper_id,
            },
        )
        self.assertEqual(
            self.jo.memberships.get().ballot, self.dulwich_post_ballot_earlier
        )

    def test_shared_ballot_stays_with_a_warning(self):
        self.jo.memberships.create(
            ballot=self.camberwell_post_ballot, party=self.labour_party
        )
        self.record(self.jo, "2026-01-02")
        self.joanne.memberships.create(
            ballot=self.camberwell_post_ballot, party=self.labour_party
        )
        self.record(self.joanne, "2026-02-02")
        self.merge(self.jo, self.joanne)
        self.jo.refresh_from_db()

        plan, restored = self.split(self.jo, self.local_ballot)
        camberwell = self.camberwell_post_ballot.ballot_paper_id
        self.assertIn(
            f"Both people stood in {camberwell}, so we can't tell whose "
            "candidacy it is. It stays where it is",
            plan.warnings,
        )
        self.assertTrue(
            self.jo.memberships.filter(
                ballot=self.camberwell_post_ballot
            ).exists()
        )

    def test_missing_merge_history_falls_back_to_plain_move(self):
        self.merge(self.jo, self.joanne)
        self.jo.refresh_from_db()
        self.jo.versions = [
            v
            for v in self.jo.versions
            if v["data"]["id"] != str(self.joanne_pk)
        ]
        self.jo.save()

        plan, new_person = self.split(self.jo, self.local_ballot)
        self.assertEqual(plan.origin.kind, "direct")
        self.assertIn(
            f"Merge history for person {self.joanne_pk} is missing, so this "
            "is treated as a direct add",
            plan.warnings,
        )
        self.assertIsNone(plan.restore_person_id)
        self.assertNotEqual(new_person.pk, self.joanne_pk)
        self.assertTrue(
            PersonRedirect.objects.filter(old_person_id=self.joanne_pk).exists()
        )

    def test_old_id_in_use_gets_new_id(self):
        self.merge(self.jo, self.joanne)
        self.jo.refresh_from_db()
        PersonFactory(pk=self.joanne_pk, name="Someone else")

        plan, restored = self.split(self.jo, self.local_ballot)
        self.assertIn(
            f"Person ID {self.joanne_pk} is in use, so the restored person "
            "gets a new ID and their history isn't copied",
            plan.warnings,
        )
        self.assertNotEqual(restored.pk, self.joanne_pk)
        self.assertEqual(restored.name, "Joanne Smith")
        self.assertEqual(len(restored.versions), 1)
        get_versions_parent_map(restored.versions)

    def test_photo_approved_before_merge(self):
        LoggedAction.objects.create(
            user=self.user,
            person=self.joanne,
            action_type=ActionType.PHOTO_APPROVE,
            popit_person_new_version=self.joanne_version,
        )
        self.merge(self.jo, self.joanne)
        self.jo.refresh_from_db()
        PersonImage.objects.create(
            person=self.jo, image="joanne.jpg", source="Council website"
        )

        with on(SPLIT_DAY):
            plan = PersonSplitter(
                self.jo, self.local_ballot, suggest=True
            ).plan()
        self.assertTrue(any("approved for person" in w for w in plan.warnings))
        self.assertFalse(plan.move_image)

        _, restored = self.split(self.jo, self.local_ballot, move_image=True)
        self.assertEqual(restored.image.image.name, "joanne.jpg")
        self.assertFalse(PersonImage.objects.filter(person=self.jo).exists())


class TestSplitDirectlyAddedCandidacy(SplitSuggestionMixin, TestCase):
    def setUp(self):
        super().setUp()
        self.jo = self.make_person(
            "Jo Smith",
            "2024-01-01",
            [(self.dulwich_post_ballot_earlier, self.labour_party)],
        )
        self.jo.memberships.create(
            ballot=self.local_ballot,
            party=self.green_party,
            sopn_first_names="Joanne",
            sopn_last_name="SMITH",
        )
        self.jo.other_names.create(name="Joanne SMITH")
        self.record(self.jo, "2024-04-01", source="SOPN")

    def test_moves_fields_added_with_the_candidacy(self):
        plan, new_person = self.split(self.jo, self.local_ballot)
        self.jo.refresh_from_db()

        self.assertEqual(plan.origin.kind, "direct")
        self.assertEqual(new_person.name, "Joanne Smith")
        self.assertEqual(
            list(new_person.other_names.values_list("name", flat=True)),
            ["Joanne SMITH"],
        )
        self.assertFalse(self.jo.other_names.exists())
        self.assertEqual(len(new_person.versions), 1)
        # Only the action for the split itself: nothing moved from the
        # original person
        self.assertEqual(
            list(
                LoggedAction.objects.filter(person=new_person).values_list(
                    "action_type", flat=True
                )
            ),
            [ActionType.PERSON_CREATE],
        )

    def test_rename_with_the_candidacy_is_undone(self):
        # Like person 65543: a councillor's record was renamed when another
        # person's candidacy was added to it, and the old name kept as an
        # other name. The SOPN fields are garbled too.
        person = self.make_person(
            "Imran Ahmed Khan",
            "2024-01-01",
            [(self.dulwich_post_ballot_earlier, self.labour_party)],
        )
        person.memberships.create(
            ballot=self.local_ballot,
            party=self.labour_party,
            sopn_first_names="KHAN",
            sopn_last_name="Khan",
        )
        person.name = "Imran Khan"
        person.save()
        person.other_names.create(name="Imran Ahmed Khan")
        self.record(person, "2024-04-01")

        plan, new_person = self.split(person, self.local_ballot)
        person.refresh_from_db()
        self.assertEqual(new_person.name, "Imran Khan")
        self.assertIn(
            "given when the candidacy was added", plan.new_person_name_source
        )
        self.assertFalse(new_person.other_names.exists())
        self.assertEqual(person.name, "Imran Ahmed Khan")
        self.assertFalse(person.other_names.exists())

    def test_name_row_shows_the_new_persons_name(self):
        # A later edit to the name used to make the row say the new person
        # gets "(nothing)", although they're always given a name
        self.jo.name = "Jo A Smith"
        self.jo.save()
        self.record(self.jo, "2024-06-01")

        with on(SPLIT_DAY):
            plan = PersonSplitter(
                self.jo, self.local_ballot, suggest=True
            ).plan()
        name = plan.suggestion_for("name")
        self.assertEqual(name.target_value, "Joanne Smith")
        self.assertEqual(name.target_value, plan.new_person_name)
        self.assertEqual(name.dest_value, "Jo A Smith")
        self.assertEqual(name.action, "keep")
        self.assertTrue(name.notable)
        self.assertIn("named from their name on the SOPN", name.reason)

    def test_name_row_copies_when_names_match(self):
        # No SOPN name and nothing added with the candidacy, so the new
        # person takes this person's name
        person = self.make_person(
            "Jo Smith",
            "2024-01-01",
            [(self.dulwich_post_ballot_earlier, self.labour_party)],
        )
        person.memberships.create(
            ballot=self.local_ballot, party=self.green_party
        )
        self.record(person, "2024-04-01")
        person.name = "Jo Smith Jr"
        person.save()
        self.record(person, "2024-06-01")

        with on(SPLIT_DAY):
            plan = PersonSplitter(
                person, self.local_ballot, suggest=True
            ).plan()
        name = plan.suggestion_for("name")
        self.assertEqual(name.target_value, "Jo Smith Jr")
        self.assertEqual(name.action, "copy")
        self.assertIn("named from this person's current name", name.reason)

    def test_moving_the_name_names_the_new_person(self):
        self.jo.name = "Jo A Smith"
        self.jo.save()
        self.record(self.jo, "2024-06-01")

        plan, new_person = self.split(
            self.jo, self.local_ballot, move_fields=["name"]
        )
        self.assertEqual(new_person.name, "Jo A Smith")
        self.jo.refresh_from_db()
        self.assertEqual(self.jo.name, "Jo Smith")

    def test_later_unrelated_edit_is_kept(self):
        self.jo.tmp_person_identifiers.create(
            value_type="email", value="jo@example.com"
        )
        self.record(self.jo, "2024-06-01")

        plan, new_person = self.split(self.jo, self.local_ballot)
        self.jo.refresh_from_db()
        email = plan.suggestion_for("email")
        self.assertEqual(email.action, "keep")
        self.assertTrue(email.notable)
        self.assertEqual(
            self.jo.get_single_identifier_value("email"), "jo@example.com"
        )
        self.assertEqual(new_person.get_single_identifier_value("email"), None)


class TestSuggestionOptions(SplitSuggestionMixin, TestCase):
    def setUp(self):
        super().setUp()
        self.jo = self.make_person(
            "Jo Smith", "2024-01-01", [(self.local_ballot, self.green_party)]
        )

    def test_suggest_cant_move_to_existing_person(self):
        plan, _ = self.split(
            self.jo, self.local_ballot, target_person=PersonFactory()
        )
        self.assertFalse(plan.is_valid)
        self.assertIn("existing person", plan.errors[0])

    def test_field_options_need_suggest(self):
        splitter = PersonSplitter(
            self.jo, self.local_ballot, move_fields=["email"]
        )
        self.assertFalse(splitter.plan().is_valid)
        with self.assertRaises(InvalidSplitError):
            splitter.split()

    def test_move_image_needs_an_image(self):
        plan, _ = self.split(self.jo, self.local_ballot, move_image=True)
        self.assertIn(f"Person {self.jo.pk} has no photo to move", plan.errors)

    def test_unknown_origin_still_splits(self):
        self.jo.versions = []
        self.jo.save()
        plan, new_person = self.split(self.jo, self.local_ballot)
        self.assertEqual(plan.origin.kind, "unknown")
        self.assertTrue(plan.warnings)
        self.assertEqual(new_person.memberships.count(), 1)
        self.assertFalse(Person.objects.get(pk=self.jo.pk).memberships.exists())
