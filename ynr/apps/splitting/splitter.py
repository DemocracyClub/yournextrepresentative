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

With `suggest=True`, the plan also uses the person's version history (see
`splitting.provenance`) to work out where the candidacy came from and suggest
what else to move. If it arrived in a merge, the merged-away person is
restored, with their old ID where possible.
"""

import copy
from dataclasses import dataclass, field
from datetime import datetime
from datetime import timezone as dt_timezone
from typing import List, Optional

from candidates.models import LoggedAction, PersonRedirect
from candidates.models.db import ActionType
from candidates.models.versions import get_person_as_version_data
from candidates.views.version_data import get_change_metadata, get_client_ip
from data_exports.models import MaterializedMemberships
from django.db import transaction
from django.template.defaultfilters import pluralize
from elections.models import Election
from people.models import Person, PersonIdentifier, PersonImage
from popolo.models import Membership
from results.models import ResultEvent
from sopn_parsing.helpers.parse_tables import clean_name
from splitting.provenance import (
    DEFAULT_CUTOFF_DAYS,
    IDENTIFIER_FIELDS,
    FieldSuggestion,
    Origin,
    apply_overrides,
    direct_add_name_hint,
    direct_add_renamed_to,
    find_origin,
    safe_timestamp,
    suggest_fields_for_direct_add,
    suggest_fields_for_merge,
)


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
    # Where the new person's name comes from, for explaining it
    new_person_name_source: str = ""
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    changes: List[str] = field(default_factory=list)

    # Only filled in when suggesting
    origin: Optional[Origin] = None
    field_suggestions: List[FieldSuggestion] = field(default_factory=list)
    restore_person_id: Optional[int] = None
    extra_memberships: List[Membership] = field(default_factory=list)
    versions_to_copy: List[dict] = field(default_factory=list)
    logged_action_ids: List[int] = field(default_factory=list)
    redirect: Optional[PersonRedirect] = None
    move_image: bool = False
    # Other names (with notes and dates) to look up details from when
    # giving names to the other person
    other_name_details: List[dict] = field(default_factory=list)

    @property
    def is_valid(self):
        return not self.errors

    @property
    def creates_person(self):
        return self.target_person is None

    @property
    def memberships_to_move(self):
        return [self.membership] + self.extra_memberships

    def suggestion_for(self, field_name):
        for suggestion in self.field_suggestions:
            if suggestion.field == field_name:
                return suggestion
        return None

    def destination_label(self, target=None):
        """
        Where the candidacy goes, as written in the split-request sheet:
        "new", a person ID, or a restored ID. Pass the person it went to
        after splitting to get a new person's ID.
        """
        if self.target_person:
            return str(self.target_person.pk)
        if self.restore_person_id:
            return f"{self.restore_person_id} (restored)"
        if target:
            return f"{target.pk} (new)"
        return "new"

    @property
    def details_to_check(self):
        """Suggestions for details edited after the candidacy arrived"""
        return [
            s
            for s in self.field_suggestions
            if s.notable and s.action == "review"
        ]

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
        suggest=False,
        cutoff_days=DEFAULT_CUTOFF_DAYS,
        move_fields=(),
        keep_fields=(),
        move_image=False,
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
        self.suggest = suggest
        self.cutoff_days = cutoff_days
        self.move_fields = list(move_fields)
        self.keep_fields = list(keep_fields)
        self.move_image = move_image

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
            plan.new_person_name_source = (
                "their name on the SOPN"
                if self.has_sopn_name(membership)
                else "this person's current name"
            )

        self.check_locked(plan, self.ballot)

        if self.suggest:
            self.plan_suggestions(plan)
        elif self.move_fields or self.keep_fields or self.move_image:
            plan.errors.append(
                "Moving or keeping fields, or moving the photo, needs "
                "suggestions turned on"
            )

        if self.target_person:
            destination = (
                f"existing person {self.target_person.pk} "
                f"({self.target_person.name})"
            )
        elif plan.restore_person_id:
            destination = (
                f"restored person {plan.restore_person_id} "
                f"'{plan.new_person_name}'"
            )
        else:
            destination = f"a new person called '{plan.new_person_name}'"
        plan.changes.insert(
            1 if plan.restore_person_id else 0,
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

    def plan_suggestions(self, plan):
        if self.target_person:
            plan.errors.append(
                "Suggestions can't be used when moving to an existing "
                "person, as they would overwrite that person's details"
            )
            return

        origin = find_origin(
            self.person.pk, self.person.versions, self.ballot.ballot_paper_id
        )
        plan.origin = origin
        plan.warnings.extend(origin.warnings)
        current_data = get_person_as_version_data(self.person)

        if origin.kind == "merge":
            self.plan_merge_restore(plan, origin, current_data)
        elif origin.kind == "direct":
            plan.field_suggestions = suggest_fields_for_direct_add(
                origin, current_data
            )
            plan.other_name_details = origin.add_version["data"].get(
                "other_names", []
            )
            if not origin.previous_version:
                plan.warnings.append(
                    f"{self.ballot.ballot_paper_id} was on person "
                    f"{self.person.pk} from their first version, so we can't "
                    "tell which details belong to whom"
                )
            # A name an editor typed when adding the candidacy beats the
            # SOPN fields, which are sometimes garbled
            renamed_to = direct_add_renamed_to(origin)
            hint = direct_add_name_hint(origin)
            if renamed_to:
                plan.new_person_name = renamed_to
                plan.new_person_name_source = (
                    "the name the person was given when the candidacy was added"
                )
            elif not self.has_sopn_name(plan.membership) and hint:
                plan.new_person_name = clean_name(hint)
                plan.new_person_name_source = (
                    "the name added with the candidacy"
                )
            self.plan_direct_add_image(plan, origin)

        missing = apply_overrides(
            plan.field_suggestions, self.move_fields, self.keep_fields
        )
        for name in missing:
            plan.errors.append(f"There's no suggestion for '{name}' to change")
        self.settle_name(plan)

        if self.move_image:
            if self.person_image():
                plan.move_image = True
                plan.changes.append(
                    f"Move the photo from {self.person.pk} to the new person"
                )
            else:
                plan.errors.append(
                    f"Person {self.person.pk} has no photo to move"
                )

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

    def settle_name(self, plan):
        """
        The other person always gets a name, so make the name suggestion say
        which one and why, rather than suggesting they get nothing
        """
        name = plan.suggestion_for("name")
        if not name:
            return
        if "name" in self.move_fields and name.target_value:
            plan.new_person_name = name.target_value
            plan.new_person_name_source = "the name moved from this person"
        name.target_value = plan.new_person_name
        if name.dest_value == name.current_value:
            name.action = (
                "copy" if plan.new_person_name == name.current_value else "keep"
            )
            name.reason = (
                "This person keeps their name. The other person is named "
                f"from {plan.new_person_name_source}"
            )
        if plan.new_person_name != name.current_value:
            name.notable = True

    def plan_merge_restore(self, plan, origin, current_data):
        person_id = self.person.pk
        merged_from = int(origin.merged_from)
        redirect = PersonRedirect.objects.filter(
            old_person_id=merged_from, new_person_id=person_id
        ).first()
        if Person.objects.filter(pk=merged_from).exists():
            plan.warnings.append(
                f"Person ID {merged_from} is in use, so the restored person "
                "gets a new ID and their history isn't copied"
            )
        elif not redirect:
            plan.warnings.append(
                f"There's no redirect from {merged_from} to {person_id}, so "
                "the restored person gets a new ID and their history isn't "
                "copied"
            )
        else:
            plan.restore_person_id = merged_from
            plan.redirect = redirect
            plan.versions_to_copy = sorted(
                origin.source_history, key=safe_timestamp, reverse=True
            )
            version_ids = [v["version_id"] for v in plan.versions_to_copy]
            plan.logged_action_ids = list(
                LoggedAction.objects.filter(
                    person=self.person,
                    popit_person_new_version__in=version_ids,
                ).values_list("id", flat=True)
            )

        plan.field_suggestions = suggest_fields_for_merge(
            origin, current_data, self.utc_now(), self.cutoff_days
        )
        plan.other_name_details = origin.source_snapshot.get("other_names", [])
        name = plan.suggestion_for("name")
        if name and name.target_value:
            plan.new_person_name = name.target_value
            plan.new_person_name_source = "their record before the merge"

        self.plan_extra_memberships(plan, origin)

        if plan.restore_person_id:
            plan.changes.insert(0, f"Restore person {merged_from} (old ID)")
            versions = len(plan.versions_to_copy)
            actions = len(plan.logged_action_ids)
            plan.changes.append(
                f"Copy {versions} version{pluralize(versions)} and move "
                f"{actions} logged action{pluralize(actions)} to "
                f"{merged_from}, and delete the redirect from {merged_from} "
                f"to {person_id}"
            )
        self.plan_merge_image(plan)

    def plan_extra_memberships(self, plan, origin):
        """
        Move the merged-away person's other candidacies with them
        """
        source_ballots = origin.source_snapshot.get("candidacies") or {}
        if not origin.dest_snapshot:
            others = set(source_ballots) - {self.ballot.ballot_paper_id}
            if others:
                plan.warnings.append(
                    "Without history from before the merge, other candidacies "
                    f"can't be divided up, so these stay: {sorted(others)}"
                )
            return
        dest_ballots = origin.dest_snapshot.get("candidacies") or {}
        for ballot_paper_id in sorted(source_ballots):
            if ballot_paper_id == self.ballot.ballot_paper_id:
                continue
            if ballot_paper_id in dest_ballots:
                plan.warnings.append(
                    f"Both people stood in {ballot_paper_id}, so we can't tell "
                    "whose candidacy it is. It stays where it is"
                )
                continue
            membership = (
                self.person.memberships.filter(
                    ballot__ballot_paper_id=ballot_paper_id
                )
                .select_related("ballot", "party")
                .first()
            )
            if not membership:
                plan.warnings.append(
                    f"The candidacy in {ballot_paper_id} was removed after "
                    "the merge, so it isn't restored"
                )
                continue
            self.check_locked(plan, membership.ballot)
            plan.extra_memberships.append(membership)
            plan.changes.append(
                f"Also move candidacy for {membership.party.name} in "
                f"{ballot_paper_id} (from person {origin.merged_from}'s "
                "history)"
            )

    def person_image(self):
        try:
            return self.person.image
        except PersonImage.DoesNotExist:
            return None

    def plan_merge_image(self, plan):
        if not self.person_image():
            return
        latest_approval = (
            LoggedAction.objects.filter(
                person=self.person, action_type=ActionType.PHOTO_APPROVE
            )
            .order_by("-created")
            .first()
        )
        source_version_ids = {
            v["version_id"] for v in plan.origin.source_history
        }
        if (
            latest_approval
            and latest_approval.popit_person_new_version in source_version_ids
        ):
            plan.warnings.append(
                "The current photo was approved for person "
                f"{plan.origin.merged_from} before the merge, so it may be "
                "theirs. You can move it with the photo option"
            )

    def plan_direct_add_image(self, plan, origin):
        added_at = origin.added_at.replace(tzinfo=dt_timezone.utc)
        if LoggedAction.objects.filter(
            person=self.person,
            action_type__in=[ActionType.PHOTO_APPROVE, ActionType.PHOTO_UPLOAD],
            created__gt=added_at,
        ).exists():
            plan.warnings.append(
                "A photo was uploaded after this candidacy was added. Check "
                "whose it is"
            )

    @staticmethod
    def utc_now():
        """Naive UTC, to compare with version timestamps"""
        return datetime.now(dt_timezone.utc).replace(tzinfo=None)

    @staticmethod
    def has_sopn_name(membership):
        return bool(membership.sopn_first_names or membership.sopn_last_name)

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
            if plan.restore_person_id:
                target = Person(
                    pk=plan.restore_person_id, name=plan.new_person_name
                )
                target.save(force_insert=True)
            elif plan.creates_person:
                target = Person.objects.create(name=plan.new_person_name)

            for membership in plan.memberships_to_move:
                target.not_standing.remove(membership.ballot.election)
                self.result_events(membership.ballot).update(winner=target)
                membership.person = target
                membership.save()

            self.apply_field_suggestions(plan, target)

            if plan.versions_to_copy:
                # Before recording the split version, so it goes on top
                target.versions = copy.deepcopy(plan.versions_to_copy)
            if plan.logged_action_ids:
                LoggedAction.objects.filter(
                    id__in=plan.logged_action_ids
                ).update(person=target)
            if plan.redirect:
                plan.redirect.delete()
            if plan.move_image:
                image = self.person.image
                image.person = target
                image.save()

            # The two people get different actions, so the recent changes
            # feed says what happened to each rather than showing two rows
            # that look the same
            if plan.restore_person_id:
                target_kind = "restored"
                target_source = (
                    f"Restored by splitting candidacy {ballot_id} off person "
                    f"{self.person.pk}"
                )
                target_action = ActionType.PERSON_CREATE
            elif plan.creates_person:
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

    def apply_field_suggestions(self, plan, target):
        """
        Give each person the value their field suggestion says they should
        end up with
        """
        if not plan.field_suggestions:
            return
        for suggestion in plan.field_suggestions:
            if suggestion.field == "name":
                # The target's name was set when they were created
                if suggestion.dest_value:
                    self.person.name = suggestion.dest_value
                continue
            if suggestion.dest_value != suggestion.current_value:
                self.apply_field(
                    self.person, suggestion.field, suggestion.dest_value, plan
                )
            if suggestion.target_value:
                self.apply_field(
                    target, suggestion.field, suggestion.target_value, plan
                )
        for person in (self.person, target):
            person.save()
            person.invalidate_identifier_cache()

    def apply_field(self, person, field_name, value, plan):
        """
        Set one field, modelled on revert_person_from_version_data
        """
        if field_name in IDENTIFIER_FIELDS:
            if value:
                PersonIdentifier.objects.update_or_create(
                    person=person,
                    value_type=field_name,
                    defaults={"value": value},
                )
            else:
                PersonIdentifier.objects.filter(
                    person=person, value_type=field_name
                ).delete()
        elif field_name == "other_names":
            person.other_names.exclude(name__in=value).delete()
            existing = set(person.other_names.values_list("name", flat=True))
            details = {on["name"]: on for on in plan.other_name_details}
            for name in value:
                if name in existing:
                    continue
                detail = details.get(name, {})
                person.other_names.create(
                    name=name,
                    note=detail.get("note") or "",
                    start_date=detail.get("start_date"),
                    end_date=detail.get("end_date"),
                )
        elif field_name == "not_standing":
            standing_in = {
                m.ballot.election.slug for m in person.memberships.all()
            }
            person.not_standing.set(
                Election.objects.filter(slug__in=value).exclude(
                    slug__in=standing_in
                )
            )
        else:
            setattr(person, field_name, value or "")
