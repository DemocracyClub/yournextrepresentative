"""
Work out where a person's candidacy came from, using only their version
history.

Everything here is a pure function over `Person.versions`-shaped data: nothing
reads or writes the database. `splitting.splitter` uses it to suggest what else
to move when splitting a candidacy off a person.

A person's versions aren't in time order once they've been merged (merging
appends the other person's whole history), so everything here sorts by
timestamp first.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional

from candidates.models.versions import is_a_merge, version_timestamp_key
from ynr_refactoring.settings import (
    SIMPLE_POPOLO_FIELDS,
    PersonIdentifierFields,
)

IDENTIFIER_FIELDS = [f.name for f in PersonIdentifierFields]

# Every field in a version's data that we compare. Candidacies are handled
# separately, as they're Membership objects rather than fields.
COMPARABLE_FIELDS = list(
    dict.fromkeys(
        [f.name for f in SIMPLE_POPOLO_FIELDS]
        + IDENTIFIER_FIELDS
        + ["other_names", "favourite_biscuit", "not_standing"]
    )
)


def safe_timestamp(version):
    """
    Parse a version's timestamp, sorting anything unparseable first rather
    than failing
    """
    try:
        return version_timestamp_key(version)
    except (KeyError, TypeError, ValueError):
        pass
    try:
        return datetime.fromisoformat(version["timestamp"])
    except (KeyError, TypeError, ValueError):
        return datetime.min


def sort_versions(versions):
    """Oldest first"""
    return sorted(versions or [], key=safe_timestamp)


def version_person_id(version):
    return str(version.get("data", {}).get("id"))


def flatten(data):
    """
    Normalise a version's data into comparable values for COMPARABLE_FIELDS
    """
    data = data or {}
    flat = {}
    for name in COMPARABLE_FIELDS:
        if name == "other_names":
            flat[name] = tuple(
                sorted(on["name"] for on in data.get("other_names") or [])
            )
        elif name == "favourite_biscuit":
            flat[name] = (data.get("extra_fields") or {}).get(
                "favourite_biscuits"
            ) or ""
        elif name == "not_standing":
            flat[name] = tuple(sorted(data.get("not_standing") or []))
        else:
            flat[name] = data.get(name) or ""
    return flat


def changed_fields(prev_data, cur_data):
    prev, cur = flatten(prev_data), flatten(cur_data)
    return {name for name in COMPARABLE_FIELDS if prev[name] != cur[name]}


def candidacy_changes(prev_data, cur_data):
    """Ballot paper IDs added, removed or changed between two versions"""
    prev = (prev_data or {}).get("candidacies") or {}
    cur = (cur_data or {}).get("candidacies") or {}
    return {
        ballot
        for ballot in set(prev) | set(cur)
        if prev.get(ballot) != cur.get(ballot)
    }


def last_set_at(history, field_name):
    """
    When `field_name` last changed to the value it has at the end of
    `history` (oldest first). None if it ends up empty.
    """
    when = None
    previous = None
    value = None
    for version in history:
        value = flatten(version["data"])[field_name]
        if when is None or value != previous:
            when = safe_timestamp(version)
        previous = value
    if not value:
        return None
    return when


def versions_belonging_to(person_id, versions):
    """
    The versions of `person_id`, plus the versions of anyone merged into them
    (and anyone merged into those, and so on), oldest first
    """
    ids = {str(person_id)}
    while True:
        merged = {
            is_a_merge(v)
            for v in versions
            if version_person_id(v) in ids and is_a_merge(v)
        }
        if merged <= ids:
            break
        ids |= merged
    return sort_versions([v for v in versions if version_person_id(v) in ids])


@dataclass
class Origin:
    kind: str  # "merge", "direct" or "unknown"
    add_version: Optional[dict] = None
    previous_version: Optional[dict] = None
    merged_from: Optional[str] = None
    source_history: List[dict] = field(default_factory=list)
    source_snapshot: Optional[dict] = None
    dest_snapshot: Optional[dict] = None
    later_versions: List[dict] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)

    @property
    def added_at(self):
        return safe_timestamp(self.add_version) if self.add_version else None

    @property
    def added_by(self):
        return self.added_by_username or "unknown user"

    @property
    def added_by_username(self):
        """The username of whoever added the candidacy, or "" if unknown"""
        return (self.add_version or {}).get("username") or ""


def find_origin(person_id, versions, ballot_paper_id):
    """
    Find the version where `ballot_paper_id` was (most recently) added to
    person `person_id`, and whether it arrived in a merge or a direct edit
    """
    person_id = str(person_id)
    versions = sort_versions(versions)
    origin = Origin(kind="unknown")
    if any(safe_timestamp(v) == datetime.min for v in versions):
        origin.warnings.append(
            "Some versions have unreadable timestamps, so ordering may be wrong"
        )

    own = [v for v in versions if version_person_id(v) == person_id]

    def has(version):
        return ballot_paper_id in (version["data"].get("candidacies") or {})

    add_index = None
    for i in range(len(own) - 1, -1, -1):
        if has(own[i]) and (i == 0 or not has(own[i - 1])):
            add_index = i
            break
    if add_index is None:
        origin.warnings.append(
            f"{ballot_paper_id} isn't in person {person_id}'s version "
            "history, so we can't tell where it came from"
        )
        return origin

    origin.add_version = own[add_index]
    origin.previous_version = own[add_index - 1] if add_index > 0 else None
    origin.later_versions = own[add_index + 1 :]
    origin.kind = "direct"

    merged_from = is_a_merge(origin.add_version)
    if not merged_from:
        return origin

    added_at = safe_timestamp(origin.add_version)
    source_own = [
        v
        for v in versions
        if version_person_id(v) == merged_from and safe_timestamp(v) <= added_at
    ]
    if not source_own or not has(source_own[-1]):
        origin.warnings.append(
            f"Merge history for person {merged_from} is missing, so this is "
            "treated as a direct add"
        )
        return origin

    origin.kind = "merge"
    origin.merged_from = merged_from
    origin.source_history = versions_belonging_to(merged_from, versions)
    origin.source_snapshot = source_own[-1]["data"]
    if origin.previous_version:
        origin.dest_snapshot = origin.previous_version["data"]
    else:
        origin.warnings.append(
            f"Person {person_id} has no history from before the merge, so "
            "we can't suggest which details belong to whom"
        )
    return origin
