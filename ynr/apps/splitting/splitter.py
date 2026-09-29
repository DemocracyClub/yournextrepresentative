"""
Tools for splitting a candidacy off a person it doesn't belong to.

This is (roughly) the inverse of `people.merging`. People end up with
candidacies that aren't theirs in two ways:

1. Two different people were merged
2. A candidacy was added to the wrong existing person, e.g. when bulk adding
   from a SOPN

In both cases the fix is to move the Membership for one ballot to another
person, either a new one or an existing one.

Splitting happens in two steps: `PersonSplitter.plan()` works out what would
happen without changing anything, and `PersonSplitter.split()` applies it.
Keeping these separate means the same plan can be shown in a management
command dry run or in a web UI before it's confirmed.
"""

from dataclasses import dataclass, field
from typing import List, Optional

from candidates.models import LoggedAction
from candidates.models.db import ActionType
from candidates.views.version_data import get_change_metadata, get_client_ip
from data_exports.models import MaterializedMemberships
from django.db import transaction
from people.models import Person
from popolo.models import Membership
from results.models import ResultEvent
from sopn_parsing.helpers.parse_tables import clean_name


class InvalidSplitError(ValueError):
    """
    Raised when splitting would cause invalid data
    """


@dataclass
class SplitPlan:
    person: Person
    membership: Optional[Membership]
    target_person: Optional[Person]
    new_person_name: str = ""
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    changes: List[str] = field(default_factory=list)

    @property
    def is_valid(self):
        return not self.errors

    @property
    def creates_person(self):
        return self.target_person is None

    @property
    def memberships_to_move(self):
        return [self.membership]

    def destination_label(self, target=None):
        """
        Where the candidacy goes, as written in the split-request sheet:
        "new" or a person ID. Pass the person it went to after splitting to
        get a new person's ID.
        """
        if self.target_person:
            return str(self.target_person.pk)
        if target:
            return f"{target.pk} (new)"
        return "new"

    @property
    def notes(self):
        """Errors, then warnings"""
        return list(self.errors) + list(self.warnings)


class PersonSplitter:
    """
    Move the candidacy on `ballot` from `person` to `target_person`, or to a
    new person if `target_person` is None.

    The Membership itself is moved rather than copied, so the result, elected
    status, party list position, previous party affiliations and SOPN names
    all go with it.
    """

    def __init__(
        self,
        person,
        ballot,
        target_person=None,
        user=None,
        request=None,
        allow_locked=False,
    ):
        """
        :type person: people.models.Person
        :type ballot: candidates.models.Ballot
        :type target_person: people.models.Person
        """
        self.person = person
        self.ballot = ballot
        self.target_person = target_person
        self.request = request
        self.user = user or (request.user if request else None)
        self.allow_locked = allow_locked

    def get_membership(self):
        return (
            self.person.memberships.filter(ballot=self.ballot)
            .select_related("ballot__election", "party")
            .first()
        )

    def new_person_name(self, membership):
        """
        Name the new person as they appear on the SOPN, if we know it
        """
        sopn_name = " ".join(
            name
            for name in [membership.sopn_first_names, membership.sopn_last_name]
            if name
        ).strip()
        if sopn_name:
            # SOPNs print last names in capitals, so clean them the same way
            # bulk adding from a SOPN does
            return clean_name(sopn_name)
        return self.person.name

    def plan(self):
        membership = self.get_membership()
        plan = SplitPlan(
            person=self.person,
            membership=membership,
            target_person=self.target_person,
        )
        ballot_id = self.ballot.ballot_paper_id

        if not membership:
            plan.errors.append(
                f"Person {self.person.pk} isn't standing in {ballot_id}"
            )
            return plan

        if self.target_person:
            if self.target_person.pk == self.person.pk:
                plan.errors.append("Can't split a person into themselves")
            elif self.target_person.memberships.filter(
                ballot__election=self.ballot.election
            ).exists():
                plan.errors.append(
                    f"Person {self.target_person.pk} is already standing in "
                    f"{self.ballot.election.slug}"
                )
        else:
            plan.new_person_name = self.new_person_name(membership)

        self.check_locked(plan, self.ballot)

        if self.target_person:
            destination = (
                f"existing person {self.target_person.pk} "
                f"({self.target_person.name})"
            )
        else:
            destination = f"a new person called '{plan.new_person_name}'"
        plan.changes.append(
            f"Move candidacy for {membership.party.name} in {ballot_id} "
            f"from {self.person.pk} ({self.person.name}) to {destination}",
        )

        if hasattr(membership, "result"):
            plan.warnings.append("The candidacy has a result, which will move")
        for moving in plan.memberships_to_move:
            result_events = self.result_events(moving.ballot)
            if result_events.exists():
                plan.changes.append(
                    f"Move {result_events.count()} result event(s) for "
                    f"{moving.ballot.ballot_paper_id}"
                )
        remaining = self.person.memberships.exclude(
            pk__in=[m.pk for m in plan.memberships_to_move]
        )
        if not remaining.exists():
            plan.warnings.append(
                f"Person {self.person.pk} will have no candidacies left"
            )
        return plan

    def check_locked(self, plan, ballot):
        """
        Moving candidacies on locked ballots is often the point of splitting,
        but it needs to be deliberate: an error unless allowed, and a warning
        when it is
        """
        if not ballot.candidates_locked:
            return
        if self.allow_locked:
            plan.warnings.append(
                f"{ballot.ballot_paper_id} is locked: this split changes a "
                "locked ballot"
            )
        else:
            plan.errors.append(
                f"{ballot.ballot_paper_id} is locked. Splitting will change a "
                "locked ballot, so this needs to be explicitly allowed"
            )

    def result_events(self, ballot=None):
        ballot = ballot or self.ballot
        return ResultEvent.objects.filter(
            winner=self.person,
            election=ballot.election,
            post=ballot.post,
        )

    def _log(self, person, change_metadata, action_type):
        LoggedAction.objects.create(
            user=self.user,
            person=person,
            ballot=self.ballot,
            action_type=action_type,
            ip_address=get_client_ip(self.request) if self.request else None,
            popit_person_new_version=change_metadata["version_id"],
            source=change_metadata["information_source"],
        )

    def split(self):
        """
        Apply the plan, returning the person the candidacy moved to
        """
        plan = self.plan()
        if not plan.is_valid:
            raise InvalidSplitError("\n".join(plan.errors))

        ballot_id = self.ballot.ballot_paper_id
        with transaction.atomic():
            target = self.target_person
            if plan.creates_person:
                target = Person.objects.create(name=plan.new_person_name)

            for membership in plan.memberships_to_move:
                target.not_standing.remove(membership.ballot.election)
                self.result_events(membership.ballot).update(winner=target)
                membership.person = target
                membership.save()

            # The two people get different actions, so the recent changes
            # feed says what happened to each rather than showing two rows
            # that look the same
            if plan.creates_person:
                target_kind = "new"
                target_source = (
                    f"Created by splitting candidacy {ballot_id} off person "
                    f"{self.person.pk}"
                )
                target_action = ActionType.PERSON_CREATE
            else:
                target_kind = "existing"
                target_source = (
                    f"Candidacy {ballot_id} moved here from person "
                    f"{self.person.pk}"
                )
                target_action = ActionType.CANDIDACY_CREATE

            source_metadata = get_change_metadata(
                self.request,
                f"After splitting candidacy {ballot_id} to {target_kind} "
                f"person {target.pk}",
                user=self.user,
            )
            self.person.record_version(source_metadata, force=True)
            self.person.save()

            target_metadata = get_change_metadata(
                self.request, target_source, user=self.user
            )
            target.record_version(target_metadata, force=True)
            target.save()

            self._log(self.person, source_metadata, ActionType.PERSON_SPLIT)
            self._log(target, target_metadata, target_action)

            MaterializedMemberships.refresh_view()
        return target
