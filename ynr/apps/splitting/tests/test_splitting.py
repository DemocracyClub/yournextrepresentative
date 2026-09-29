from candidates.models import LoggedAction
from candidates.models.db import ActionType
from candidates.tests.auth import TestUserMixin
from candidates.tests.uk_examples import UK2015ExamplesMixin
from django.test import TestCase
from people.models import Person
from people.tests.factories import PersonFactory
from results.models import ResultEvent
from splitting.splitter import InvalidSplitError, PersonSplitter


class TestPersonSplitter(TestUserMixin, UK2015ExamplesMixin, TestCase):
    def setUp(self):
        super().setUp()
        self.person = PersonFactory(name="Jo Smith")
        self.person.memberships.create(
            ballot=self.dulwich_post_ballot_earlier, party=self.labour_party
        )
        self.wrong_membership = self.person.memberships.create(
            ballot=self.local_ballot,
            party=self.green_party,
            sopn_first_names="Joanne",
            sopn_last_name="SMITH",
        )

    def test_split_to_new_person(self):
        splitter = PersonSplitter(
            self.person, self.local_ballot, user=self.user
        )
        new_person = splitter.split()

        self.assertNotEqual(new_person.pk, self.person.pk)
        self.assertEqual(new_person.name, "Joanne Smith")
        self.wrong_membership.refresh_from_db()
        self.assertEqual(self.wrong_membership.person, new_person)
        self.assertEqual(
            list(
                self.person.memberships.values_list(
                    "ballot__ballot_paper_id", flat=True
                )
            ),
            [self.dulwich_post_ballot_earlier.ballot_paper_id],
        )

    def test_new_person_name_keeps_mixed_case_sopn_name(self):
        self.wrong_membership.sopn_first_names = "Jo"
        self.wrong_membership.sopn_last_name = "Smith"
        self.wrong_membership.save()
        new_person = PersonSplitter(self.person, self.local_ballot).split()
        self.assertEqual(new_person.name, "Jo Smith")

    def test_new_person_name_falls_back_to_person_name(self):
        self.wrong_membership.sopn_first_names = ""
        self.wrong_membership.sopn_last_name = ""
        self.wrong_membership.save()
        new_person = PersonSplitter(self.person, self.local_ballot).split()
        self.assertEqual(new_person.name, "Jo Smith")

    def test_split_records_versions_and_logged_actions(self):
        new_person = PersonSplitter(
            self.person, self.local_ballot, user=self.user
        ).split()
        self.person.refresh_from_db()
        ballot_id = self.local_ballot.ballot_paper_id

        self.assertEqual(
            self.person.versions[0]["information_source"],
            f"After splitting candidacy {ballot_id} to new person "
            f"{new_person.pk}",
        )
        self.assertNotIn(
            ballot_id, self.person.versions[0]["data"]["candidacies"]
        )
        self.assertEqual(
            new_person.versions[0]["information_source"],
            f"Created by splitting candidacy {ballot_id} off person "
            f"{self.person.pk}",
        )
        self.assertIn(ballot_id, new_person.versions[0]["data"]["candidacies"])
        self.assertEqual(new_person.versions[0]["username"], self.user.username)

        # One action per person, of different types, so recent changes
        # doesn't show two identical rows
        self.assertEqual(
            {
                (a.person_id, a.action_type, a.ballot_id, a.user_id)
                for a in LoggedAction.objects.all()
            },
            {
                (
                    self.person.pk,
                    ActionType.PERSON_SPLIT,
                    self.local_ballot.pk,
                    self.user.pk,
                ),
                (
                    new_person.pk,
                    ActionType.PERSON_CREATE,
                    self.local_ballot.pk,
                    self.user.pk,
                ),
            },
        )
        for action in LoggedAction.objects.all():
            self.assertEqual(
                action.person.versions[0]["version_id"],
                action.popit_person_new_version,
            )

    def test_split_to_existing_person(self):
        other = PersonFactory(name="Joanne Smith")
        other.not_standing.add(self.local_election)

        target = PersonSplitter(
            self.person, self.local_ballot, target_person=other
        ).split()

        self.assertEqual(target, other)
        self.assertEqual(Person.objects.count(), 2)
        self.assertEqual(other.memberships.get(), self.wrong_membership)
        self.assertFalse(other.not_standing.exists())
        ballot_id = self.local_ballot.ballot_paper_id
        other_action = LoggedAction.objects.get(person=other)
        self.assertEqual(other_action.action_type, ActionType.CANDIDACY_CREATE)
        self.assertEqual(
            other_action.source,
            f"Candidacy {ballot_id} moved here from person {self.person.pk}",
        )
        self.assertEqual(
            LoggedAction.objects.get(person=self.person).source,
            f"After splitting candidacy {ballot_id} to existing person "
            f"{other.pk}",
        )

    def test_result_events_move(self):
        self.wrong_membership.elected = True
        self.wrong_membership.save()
        ResultEvent.objects.create(
            election=self.local_election,
            winner=self.person,
            post=self.local_post,
            old_post_id=self.local_post.slug,
            winner_party=self.green_party,
            source="Council website",
        )
        new_person = PersonSplitter(self.person, self.local_ballot).split()

        self.assertEqual(ResultEvent.objects.get().winner, new_person)
        self.wrong_membership.refresh_from_db()
        self.assertTrue(self.wrong_membership.elected)

    def test_person_not_on_ballot(self):
        plan = PersonSplitter(self.person, self.camberwell_post_ballot).plan()
        self.assertFalse(plan.is_valid)
        with self.assertRaises(InvalidSplitError):
            PersonSplitter(self.person, self.camberwell_post_ballot).split()

    def test_target_already_standing_in_election(self):
        other = PersonFactory()
        other.memberships.create(
            ballot=self.local_ballot, party=self.labour_party
        )
        splitter = PersonSplitter(
            self.person, self.local_ballot, target_person=other
        )
        self.assertIn(
            f"Person {other.pk} is already standing in "
            f"{self.local_election.slug}",
            splitter.plan().errors,
        )
        with self.assertRaises(InvalidSplitError):
            splitter.split()
        self.wrong_membership.refresh_from_db()
        self.assertEqual(self.wrong_membership.person, self.person)

    def test_cant_split_into_self(self):
        splitter = PersonSplitter(
            self.person, self.local_ballot, target_person=self.person
        )
        self.assertFalse(splitter.plan().is_valid)

    def test_locked_ballot_needs_allow_locked(self):
        self.local_ballot.candidates_locked = True
        self.local_ballot.save()

        self.assertFalse(
            PersonSplitter(self.person, self.local_ballot).plan().is_valid
        )
        new_person = PersonSplitter(
            self.person, self.local_ballot, allow_locked=True
        ).split()
        self.assertEqual(new_person.memberships.get(), self.wrong_membership)

    def test_locked_ballot_to_existing_person_needs_allow_locked(self):
        self.local_ballot.candidates_locked = True
        self.local_ballot.save()
        other = PersonFactory()

        self.assertFalse(
            PersonSplitter(self.person, self.local_ballot, target_person=other)
            .plan()
            .is_valid
        )
        PersonSplitter(
            self.person,
            self.local_ballot,
            target_person=other,
            allow_locked=True,
        ).split()
        self.assertEqual(other.memberships.get(), self.wrong_membership)

    def test_logged_action_description(self):
        PersonSplitter(self.person, self.local_ballot, user=self.user).split()
        action = LoggedAction.objects.get(action_type=ActionType.PERSON_SPLIT)
        self.assertEqual(action.person, self.person)
        self.assertEqual(
            action.friendly_description(),
            f"User <strong>{self.user.username}</strong> split a candidacy "
            f'off <a href="/person/{self.person.pk}">'
            f"candidate #{self.person.pk}</a>",
        )

    def test_warns_when_no_candidacies_left(self):
        self.person.memberships.exclude(pk=self.wrong_membership.pk).delete()
        plan = PersonSplitter(self.person, self.local_ballot).plan()
        self.assertTrue(plan.is_valid)
        self.assertIn(
            f"Person {self.person.pk} will have no candidacies left",
            plan.warnings,
        )
