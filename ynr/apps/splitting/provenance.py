"""
Work out where a person's candidacy came from, and which of their details
belong to which real person, using only their version history.

Everything here is a pure function over `Person.versions`-shaped data: nothing
reads or writes the database. `splitting.splitter` uses it to suggest what else
to move when splitting a candidacy off a person.

A person's versions aren't in time order once they've been merged (merging
appends the other person's whole history), so everything here sorts by
timestamp first.
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any, List, Optional

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

# Fields that go stale, so we only restore them if they were set recently.
# Everything else (name, gender, birth date...) is always restored, because a
# restored person needs a name and biographical facts don't expire.
# This is a product decision, so change it if the team disagrees.
CUTOFF_FIELDS = IDENTIFIER_FIELDS + ["biography"]

DEFAULT_CUTOFF_DAYS = 365


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


@dataclass
class FieldSuggestion:
    field: str
    # "keep", "move", "copy", "drop", "restore" or "review"
    action: str
    # What the other person (restored or new) gets. Empty means nothing.
    target_value: Any
    # What the original person ends up with
    dest_value: Any
    reason: str
    # The original person's value now, and before the candidacy arrived.
    # Used when an operator overrides the suggestion.
    current_value: Any = ""
    dest_before: Any = ""
    # False for rows not worth showing an operator (nothing to restore)
    notable: bool = True


def field_edits(origin):
    """
    The latest edit to each field after the candidacy arrived, as
    {field: version}
    """
    edits = {}
    previous = origin.add_version
    for version in origin.later_versions:
        for name in changed_fields(previous["data"], version["data"]):
            edits[name] = version
        previous = version
    return edits


def describe_edit(version):
    when = safe_timestamp(version).date().isoformat()
    who = version.get("username") or "unknown user"
    source = (version.get("information_source") or "").strip()
    text = f"edited on {when} by {who}"
    if source:
        text += f': "{source[:80]}"'
    return text


def suggest_fields_for_merge(origin, current_data, now, cutoff_days):
    """
    Suggest how to divide each field between the original person and the
    person being restored. See section 5.3 of PERSON-SPLITTING-DESIGN.md.

    `now` is a naive UTC datetime, to compare with version timestamps.
    """
    if origin.kind != "merge" or not origin.dest_snapshot:
        return []

    S = flatten(origin.source_snapshot)
    D = flatten(origin.dest_snapshot)
    C = flatten(current_data)
    cutoff = now - timedelta(days=cutoff_days)
    edits = field_edits(origin)

    def within_cutoff(name):
        if name not in CUTOFF_FIELDS:
            return True
        set_at = last_set_at(origin.source_history, name)
        return set_at is not None and set_at >= cutoff

    def too_old(name):
        set_at = last_set_at(origin.source_history, name)
        when = set_at.date().isoformat() if set_at else "unknown"
        return f"last set {when}, older than {cutoff_days} days"

    def review_reason(name):
        if name in edits:
            return (
                f"{describe_edit(edits[name])} after the merge: check which "
                "person it belongs to"
            )
        return "changed after the merge: check which person it belongs to"

    suggestions = []
    for name in COMPARABLE_FIELDS:
        s, d, c = S[name], D[name], C[name]
        base = {"field": name, "current_value": c, "dest_before": d}

        if name == "name":
            suggestions.append(_suggest_name(s, d, c, base, review_reason))
            continue
        if name == "other_names":
            suggestions.append(_suggest_other_names(S, D, C, base))
            continue
        if name == "not_standing":
            removed = tuple(e for e in s if e not in d)
            suggestions.append(
                FieldSuggestion(
                    action="move" if removed else ("copy" if s else "keep"),
                    target_value=s,
                    dest_value=tuple(e for e in c if e not in removed),
                    reason="elections the other person wasn't standing in",
                    notable=bool(s),
                    **base,
                )
            )
            continue

        if not s:
            suggestions.append(
                FieldSuggestion(
                    action="keep",
                    target_value="",
                    dest_value=c,
                    reason="other person had no value",
                    notable=False,
                    **base,
                )
            )
        elif c == s and s != d:
            if within_cutoff(name):
                suggestions.append(
                    FieldSuggestion(
                        action="move",
                        target_value=s,
                        dest_value=d,
                        reason="value came from the merge",
                        **base,
                    )
                )
            else:
                suggestions.append(
                    FieldSuggestion(
                        action="drop",
                        target_value="",
                        dest_value=d,
                        reason=f"value came from the merge, but {too_old(name)}",
                        **base,
                    )
                )
        elif c == d:
            if within_cutoff(name):
                suggestions.append(
                    FieldSuggestion(
                        action="copy",
                        target_value=s,
                        dest_value=c,
                        reason="restored from pre-merge history",
                        **base,
                    )
                )
            else:
                suggestions.append(
                    FieldSuggestion(
                        action="drop",
                        target_value="",
                        dest_value=c,
                        reason=too_old(name),
                        **base,
                    )
                )
        else:
            suggestions.append(
                FieldSuggestion(
                    action="review",
                    target_value=s if within_cutoff(name) else "",
                    dest_value=c,
                    reason=review_reason(name),
                    **base,
                )
            )
    return suggestions


def _suggest_name(s, d, c, base, review_reason):
    """
    Undo PersonMerger.merge_name_and_other_names, which keeps the shorter of
    the two names
    """
    if c == s and s != d:
        return FieldSuggestion(
            action="move",
            target_value=s,
            dest_value=d,
            reason="the merge kept the other person's (shorter) name",
            **base,
        )
    if c == d or s == d:
        return FieldSuggestion(
            action="copy",
            target_value=s,
            dest_value=c,
            reason="restored from pre-merge history",
            notable=s != c,
            **base,
        )
    return FieldSuggestion(
        action="review",
        target_value=s,
        dest_value=c,
        reason=review_reason("name"),
        **base,
    )


def _suggest_other_names(S, D, C, base):
    """
    The merge adds the longer name, and all of the other person's other names,
    to the original person. Take those back off.
    """
    from_merge = {S["name"], D["name"]} | set(S["other_names"])
    added_since = set(C["other_names"]) - set(D["other_names"])
    removed = added_since & from_merge
    dest = tuple(n for n in C["other_names"] if n not in removed)
    if removed and S["other_names"]:
        action = "move"
        reason = "names added by the merge go back to the other person"
    elif removed:
        # Only the other person's name was added, and it's their name again
        action = "restore"
        reason = "the merge added the other person's name here; it's removed"
    elif S["other_names"]:
        action = "copy"
        reason = "the other person's other names from before the merge"
    else:
        action = "keep"
        reason = "names added by the merge"
    return FieldSuggestion(
        action=action,
        target_value=S["other_names"],
        dest_value=dest,
        reason=reason,
        notable=bool(removed or S["other_names"]),
        **base,
    )


def suggest_fields_for_direct_add(origin, current_data):
    """
    Suggest moving whatever changed in the same edit that added the
    candidacy. See section 5.4 of PERSON-SPLITTING-DESIGN.md.
    """
    if origin.kind != "direct" or not origin.previous_version:
        return []

    P = flatten(origin.previous_version["data"])
    A = flatten(origin.add_version["data"])
    C = flatten(current_data)
    added_with = changed_fields(
        origin.previous_version["data"], origin.add_version["data"]
    )
    edits = field_edits(origin)

    suggestions = []
    for name in COMPARABLE_FIELDS:
        if name == "not_standing":
            continue
        base = {"field": name, "current_value": C[name], "dest_before": P[name]}
        if name == "other_names" and name in added_with:
            # When the edit also renamed the person, their old name was
            # usually kept as an other name. That's the original person's
            # name, so it doesn't go to the new person.
            renamed = A["name"] != P["name"]
            old_name = P["name"] if renamed else None
            added = tuple(
                n for n in A[name] if n not in P[name] and n != old_name
            )
            dest = tuple(n for n in C[name] if n not in added)
            if renamed and C["name"] == A["name"]:
                # The rename is being undone, so the old name is their name
                # again rather than an other name
                dest = tuple(n for n in dest if n != old_name)
            suggestions.append(
                FieldSuggestion(
                    action="move" if added else "restore",
                    target_value=added,
                    dest_value=dest,
                    reason=(
                        "added in the same edit as the candidacy"
                        if added
                        else "the old name, kept when the person was renamed"
                    ),
                    **base,
                )
            )
        elif name in added_with:
            if C[name] == A[name] and not A[name]:
                # The edit cleared this field, so there's nothing to give
                # the other person: just undo the clearing
                suggestions.append(
                    FieldSuggestion(
                        action="restore",
                        target_value="",
                        dest_value=P[name],
                        reason=(
                            "removed in the same edit as the candidacy; put "
                            "back on this person"
                        ),
                        **base,
                    )
                )
            elif C[name] == A[name]:
                suggestions.append(
                    FieldSuggestion(
                        action="move",
                        target_value=A[name],
                        dest_value=P[name],
                        reason="changed in the same edit as the candidacy",
                        **base,
                    )
                )
            else:
                reason = "changed in the same edit as the candidacy"
                if name in edits:
                    reason += f", then {describe_edit(edits[name])}"
                suggestions.append(
                    FieldSuggestion(
                        action="review",
                        target_value=A[name],
                        dest_value=C[name],
                        reason=reason,
                        **base,
                    )
                )
        elif name in edits:
            suggestions.append(
                FieldSuggestion(
                    action="keep",
                    target_value="",
                    dest_value=C[name],
                    reason=(
                        f"{describe_edit(edits[name])} after the candidacy "
                        "was added; kept on the original person"
                    ),
                    # Edited, but empty now: nothing for anyone to decide
                    notable=bool(C[name]),
                    **base,
                )
            )
        else:
            # Not touched since before the candidacy: nothing to decide, but
            # keep a row so operators can still override it
            suggestions.append(
                FieldSuggestion(
                    action="keep",
                    target_value="",
                    dest_value=C[name],
                    reason="unchanged by the candidacy",
                    notable=False,
                    **base,
                )
            )
    return suggestions


def direct_add_renamed_to(origin):
    """
    The name the person was given in the edit that added the candidacy, if
    that edit renamed them. An editor typed it for this candidacy, so it's
    the best name for the new person.
    """
    if origin.kind != "direct" or not origin.previous_version:
        return ""
    P = flatten(origin.previous_version["data"])
    A = flatten(origin.add_version["data"])
    if A["name"] != P["name"]:
        return A["name"]
    return ""


def direct_add_name_hint(origin):
    """
    A name for the new person from an other name added with the candidacy
    (usually the SOPN name), ignoring the person's old name if they were
    renamed at the same time
    """
    if origin.kind != "direct" or not origin.previous_version:
        return ""
    P = flatten(origin.previous_version["data"])
    A = flatten(origin.add_version["data"])
    added = [
        n
        for n in A["other_names"]
        if n not in P["other_names"] and n != P["name"]
    ]
    if added:
        return added[0]
    return direct_add_renamed_to(origin)


def apply_overrides(suggestions, move_fields=(), keep_fields=()):
    """
    Force suggestions for named fields, returning the names that had no
    suggestion to override.

    Moving gives the other person the current value and returns the original
    person to their earlier value; keeping leaves everything on the original
    person.
    """
    by_field = {s.field: s for s in suggestions}
    missing = []
    for name in move_fields:
        if name not in by_field:
            missing.append(name)
            continue
        s = by_field[name]
        s.action = "move"
        s.target_value = s.current_value
        s.dest_value = s.dest_before
        s.reason = "you chose to move the current value"
        s.notable = True
    for name in keep_fields:
        if name not in by_field:
            missing.append(name)
            continue
        s = by_field[name]
        s.action = "keep"
        s.target_value = () if isinstance(s.current_value, tuple) else ""
        s.dest_value = s.current_value
        s.reason = "you chose to keep it on this person"
        s.notable = True
    return missing
