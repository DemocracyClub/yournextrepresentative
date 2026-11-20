from datetime import datetime

from django.test import SimpleTestCase
from splitting.provenance import (
    COMPARABLE_FIELDS,
    apply_overrides,
    changed_fields,
    direct_add_name_hint,
    find_origin,
    flatten,
    last_set_at,
    suggest_fields_for_direct_add,
    suggest_fields_for_merge,
    versions_belonging_to,
)

BALLOT = "local.foo.bar.2024-05-02"
OTHER_BALLOT = "parl.dulwich.2019-12-12"
NOW = datetime(2026, 9, 28)


def version(
    person_id,
    timestamp,
    source="An edit",
    ballots=(),
    username="alice",
    **fields,
):
    data = {
        "id": str(person_id),
        "name": "Jo Smith",
        "candidacies": {b: {"party": "PP53"} for b in ballots},
    }
    if "other_names" in fields:
        fields["other_names"] = [{"name": n} for n in fields["other_names"]]
    data.update(fields)
    return {
        "version_id": f"{person_id}-{timestamp}",
        "timestamp": f"{timestamp}T12:00:00.000000",
        "username": username,
        "information_source": source,
        "data": data,
    }


def merged(source_id, timestamp, dest_id=1, **kwargs):
    return version(
        dest_id, timestamp, source=f"After merging person {source_id}", **kwargs
    )


def suggestions_by_field(suggestions):
    return {s.field: s for s in suggestions}


class TestHelpers(SimpleTestCase):
    def test_flatten_normalises_fields(self):
        flat = flatten(
            {
                "name": "Jo",
                "other_names": [{"name": "Zed"}, {"name": "Amy"}],
                "extra_fields": {"favourite_biscuits": "Hobnob"},
                "not_standing": ["b", "a"],
            }
        )
        self.assertEqual(flat["name"], "Jo")
        self.assertEqual(flat["other_names"], ("Amy", "Zed"))
        self.assertEqual(flat["favourite_biscuit"], "Hobnob")
        self.assertEqual(flat["not_standing"], ("a", "b"))
        self.assertEqual(flat["email"], "")

    def test_comparable_fields_have_no_duplicates(self):
        self.assertEqual(len(COMPARABLE_FIELDS), len(set(COMPARABLE_FIELDS)))
        self.assertIn("email", COMPARABLE_FIELDS)
        self.assertNotIn("candidacies", COMPARABLE_FIELDS)

    def test_changed_fields(self):
        self.assertEqual(
            changed_fields(
                {"name": "Jo", "email": ""},
                {"name": "Jo", "email": "jo@example.com"},
            ),
            {"email"},
        )

    def test_last_set_at(self):
        history = [
            version(2, "2020-01-01", email="old@example.com"),
            version(2, "2021-01-01", email="new@example.com"),
            version(2, "2022-01-01", email="new@example.com", gender="f"),
        ]
        self.assertEqual(
            last_set_at(history, "email"), datetime(2021, 1, 1, 12)
        )
        self.assertIsNone(last_set_at(history, "biography"))

    def test_versions_belonging_to_follows_merge_chains(self):
        versions = [
            version(3, "2020-01-01"),
            version(2, "2020-06-01"),
            version(2, "2021-01-01", source="After merging person 3"),
            version(1, "2020-01-01"),
            merged(2, "2022-01-01"),
        ]
        ids = [v["data"]["id"] for v in versions_belonging_to(2, versions)]
        self.assertEqual(ids, ["3", "2", "2"])


class TestFindOrigin(SimpleTestCase):
    def test_direct_add(self):
        versions = [
            version(1, "2020-01-01", ballots=[OTHER_BALLOT]),
            version(1, "2024-04-01", ballots=[OTHER_BALLOT, BALLOT]),
            version(1, "2024-05-01", ballots=[OTHER_BALLOT, BALLOT]),
        ]
        origin = find_origin(1, versions, BALLOT)
        self.assertEqual(origin.kind, "direct")
        self.assertEqual(origin.add_version, versions[1])
        self.assertEqual(origin.previous_version, versions[0])
        self.assertEqual(origin.later_versions, [versions[2]])

    def test_versions_out_of_order_are_sorted(self):
        versions = [
            version(1, "2024-04-01", ballots=[BALLOT]),
            version(1, "2020-01-01"),
        ]
        origin = find_origin(1, versions, BALLOT)
        self.assertEqual(origin.add_version["timestamp"][:10], "2024-04-01")

    def test_removed_then_re_added_picks_latest_addition(self):
        versions = [
            version(1, "2020-01-01"),
            version(1, "2021-01-01", ballots=[BALLOT]),
            version(1, "2022-01-01"),
            version(1, "2023-01-01", ballots=[BALLOT]),
        ]
        origin = find_origin(1, versions, BALLOT)
        self.assertEqual(origin.add_version, versions[3])
        self.assertEqual(origin.previous_version, versions[2])

    def test_ballot_in_first_version(self):
        versions = [version(1, "2024-04-01", ballots=[BALLOT])]
        origin = find_origin(1, versions, BALLOT)
        self.assertEqual(origin.kind, "direct")
        self.assertIsNone(origin.previous_version)

    def test_ballot_not_in_history(self):
        origin = find_origin(1, [version(1, "2020-01-01")], BALLOT)
        self.assertEqual(origin.kind, "unknown")
        self.assertTrue(origin.warnings)

    def test_merge_with_full_history(self):
        versions = [
            version(1, "2020-01-01", ballots=[OTHER_BALLOT]),
            merged(2, "2024-05-01", ballots=[OTHER_BALLOT, BALLOT]),
            version(2, "2024-04-01", ballots=[BALLOT], email="jo@example.com"),
        ]
        origin = find_origin(1, versions, BALLOT)
        self.assertEqual(origin.kind, "merge")
        self.assertEqual(origin.merged_from, "2")
        self.assertEqual(origin.source_snapshot["email"], "jo@example.com")
        self.assertEqual(origin.dest_snapshot, versions[0]["data"])
        self.assertEqual(origin.source_history, [versions[2]])

    def test_merge_with_missing_source_history(self):
        versions = [
            version(1, "2020-01-01"),
            merged(2, "2024-05-01", ballots=[BALLOT]),
        ]
        origin = find_origin(1, versions, BALLOT)
        self.assertEqual(origin.kind, "direct")
        self.assertIn(
            "Merge history for person 2 is missing", origin.warnings[0]
        )

    def test_merge_where_source_had_its_own_merge(self):
        versions = [
            version(1, "2020-01-01"),
            version(3, "2021-01-01", email="three@example.com"),
            version(2, "2022-01-01", ballots=[BALLOT]),
            version(
                2,
                "2023-01-01",
                source="After merging person 3",
                ballots=[BALLOT],
            ),
            merged(2, "2024-01-01", ballots=[BALLOT]),
        ]
        origin = find_origin(1, versions, BALLOT)
        self.assertEqual(origin.kind, "merge")
        self.assertEqual(
            [v["data"]["id"] for v in origin.source_history], ["3", "2", "2"]
        )
        self.assertEqual(origin.source_snapshot, versions[3]["data"])

    def test_merge_with_no_pre_merge_dest_history(self):
        versions = [
            version(2, "2024-04-01", ballots=[BALLOT]),
            merged(2, "2024-05-01", ballots=[BALLOT]),
        ]
        origin = find_origin(1, versions, BALLOT)
        self.assertEqual(origin.kind, "merge")
        self.assertIsNone(origin.dest_snapshot)
        self.assertTrue(origin.warnings)
        self.assertEqual(suggest_fields_for_merge(origin, {}, NOW, 365), [])


class TestMergeSuggestions(SimpleTestCase):
    def origin(self, dest_fields, source_fields, later=()):
        versions = [
            version(1, "2026-01-01", ballots=[OTHER_BALLOT], **dest_fields),
            version(2, "2026-02-01", ballots=[BALLOT], **source_fields),
            merged(2, "2026-03-01", ballots=[OTHER_BALLOT, BALLOT]),
            *later,
        ]
        return find_origin(1, versions, BALLOT)

    def suggest(self, origin, current, cutoff_days=365):
        return suggestions_by_field(
            suggest_fields_for_merge(origin, current, NOW, cutoff_days)
        )

    def test_source_had_no_value(self):
        origin = self.origin({"email": "a@example.com"}, {})
        s = self.suggest(origin, {"email": "a@example.com"})["email"]
        self.assertEqual(s.action, "keep")
        self.assertFalse(s.notable)

    def test_value_came_from_the_merge(self):
        origin = self.origin({}, {"email": "b@example.com"})
        s = self.suggest(origin, {"email": "b@example.com"})["email"]
        self.assertEqual(s.action, "move")
        self.assertEqual(s.target_value, "b@example.com")
        self.assertEqual(s.dest_value, "")

    def test_value_came_from_the_merge_but_is_too_old(self):
        origin = self.origin({}, {"email": "b@example.com"})
        s = self.suggest(origin, {"email": "b@example.com"}, cutoff_days=30)[
            "email"
        ]
        self.assertEqual(s.action, "drop")
        self.assertEqual(s.target_value, "")
        self.assertEqual(s.dest_value, "")
        self.assertIn("older than 30 days", s.reason)

    def test_cutoff_only_applies_to_stale_fields(self):
        origin = self.origin({}, {"gender": "female"})
        s = self.suggest(origin, {"gender": "female"}, cutoff_days=1)["gender"]
        self.assertEqual(s.action, "move")

    def test_dest_kept_its_value(self):
        origin = self.origin(
            {"twitter_username": "jo1"}, {"twitter_username": "jo2"}
        )
        s = self.suggest(origin, {"twitter_username": "jo1"})[
            "twitter_username"
        ]
        self.assertEqual(s.action, "copy")
        self.assertEqual(s.target_value, "jo2")
        self.assertEqual(s.dest_value, "jo1")

    def test_edited_after_the_merge_needs_review(self):
        later = [
            version(
                1,
                "2026-04-01",
                source="Found on council site",
                ballots=[OTHER_BALLOT, BALLOT],
                email="c@example.com",
                username="bob",
            )
        ]
        origin = self.origin(
            {"email": "a@example.com"}, {"email": "b@example.com"}, later
        )
        s = self.suggest(origin, {"email": "c@example.com"})["email"]
        self.assertEqual(s.action, "review")
        self.assertEqual(s.dest_value, "c@example.com")
        self.assertIn("2026-04-01 by bob", s.reason)
        self.assertIn("Found on council site", s.reason)

    def test_name_undoes_the_merge(self):
        origin = self.origin({"name": "Joanne Smith"}, {"name": "Jo Smith"})
        suggestions = self.suggest(
            origin,
            {"name": "Jo Smith", "other_names": [{"name": "Joanne Smith"}]},
        )
        self.assertEqual(suggestions["name"].action, "move")
        self.assertEqual(suggestions["name"].target_value, "Jo Smith")
        self.assertEqual(suggestions["name"].dest_value, "Joanne Smith")
        self.assertEqual(suggestions["other_names"].action, "restore")
        self.assertEqual(suggestions["other_names"].dest_value, ())

    def test_other_names_moved_by_the_merge_go_back(self):
        origin = self.origin(
            {"other_names": ["Jo S"]}, {"other_names": ["Jojo"]}
        )
        s = self.suggest(
            origin, {"other_names": [{"name": "Jo S"}, {"name": "Jojo"}]}
        )["other_names"]
        self.assertEqual(s.target_value, ("Jojo",))
        self.assertEqual(s.dest_value, ("Jo S",))

    def test_not_standing_added_by_the_merge_goes_back(self):
        origin = self.origin({}, {"not_standing": ["parl.2024-07-04"]})
        s = self.suggest(origin, {"not_standing": ["parl.2024-07-04"]})[
            "not_standing"
        ]
        self.assertEqual(s.action, "move")
        self.assertEqual(s.target_value, ("parl.2024-07-04",))
        self.assertEqual(s.dest_value, ())


class TestDirectAddSuggestions(SimpleTestCase):
    def setUp(self):
        self.versions = [
            version(1, "2020-01-01", ballots=[OTHER_BALLOT]),
            version(
                1,
                "2024-04-01",
                ballots=[OTHER_BALLOT, BALLOT],
                other_names=["Joanne SMITH"],
            ),
        ]

    def test_fields_added_with_the_candidacy_move(self):
        origin = find_origin(1, self.versions, BALLOT)
        suggestions = suggestions_by_field(
            suggest_fields_for_direct_add(
                origin, {"other_names": [{"name": "Joanne SMITH"}]}
            )
        )
        s = suggestions["other_names"]
        self.assertEqual(s.action, "move")
        self.assertEqual(s.target_value, ("Joanne SMITH",))
        self.assertEqual(s.dest_value, ())
        self.assertFalse(suggestions["email"].notable)
        self.assertEqual(direct_add_name_hint(origin), "Joanne SMITH")

    def test_later_unrelated_edit_is_kept_but_shown(self):
        self.versions.append(
            version(
                1,
                "2024-06-01",
                ballots=[OTHER_BALLOT, BALLOT],
                other_names=["Joanne SMITH"],
                email="jo@example.com",
            )
        )
        origin = find_origin(1, self.versions, BALLOT)
        s = suggestions_by_field(
            suggest_fields_for_direct_add(
                origin,
                {
                    "other_names": [{"name": "Joanne SMITH"}],
                    "email": "jo@example.com",
                },
            )
        )["email"]
        self.assertEqual(s.action, "keep")
        self.assertTrue(s.notable)
        self.assertIn("after the candidacy was added", s.reason)

    def test_field_cleared_with_the_candidacy_is_restored(self):
        versions = [
            version(1, "2020-01-01", ballots=[OTHER_BALLOT], biography="Bio"),
            version(1, "2024-04-01", ballots=[OTHER_BALLOT, BALLOT]),
        ]
        origin = find_origin(1, versions, BALLOT)
        s = suggestions_by_field(suggest_fields_for_direct_add(origin, {}))[
            "biography"
        ]
        self.assertEqual(s.action, "restore")
        self.assertEqual(s.target_value, "")
        self.assertEqual(s.dest_value, "Bio")

    def test_later_edit_to_an_empty_field_is_hidden(self):
        self.versions.append(
            version(
                1,
                "2024-06-01",
                ballots=[OTHER_BALLOT, BALLOT],
                other_names=["Joanne SMITH"],
                honorific_suffix="MP",
            )
        )
        self.versions.append(
            version(
                1,
                "2024-07-01",
                ballots=[OTHER_BALLOT, BALLOT],
                other_names=["Joanne SMITH"],
            )
        )
        origin = find_origin(1, self.versions, BALLOT)
        s = suggestions_by_field(
            suggest_fields_for_direct_add(
                origin, {"other_names": [{"name": "Joanne SMITH"}]}
            )
        )["honorific_suffix"]
        self.assertEqual(s.action, "keep")
        self.assertFalse(s.notable)

    def test_no_suggestions_when_candidacy_was_there_from_the_start(self):
        origin = find_origin(
            1, [version(1, "2024-04-01", ballots=[BALLOT])], BALLOT
        )
        self.assertEqual(suggest_fields_for_direct_add(origin, {}), [])


class TestOverrides(SimpleTestCase):
    def test_move_and_keep(self):
        versions = [
            version(1, "2026-01-01", ballots=[OTHER_BALLOT], email="a@x.com"),
            version(2, "2026-02-01", ballots=[BALLOT], gender="f"),
            merged(2, "2026-03-01", ballots=[OTHER_BALLOT, BALLOT]),
            version(
                1, "2026-04-01", ballots=[OTHER_BALLOT, BALLOT], email="c@x.com"
            ),
        ]
        origin = find_origin(1, versions, BALLOT)
        suggestions = suggest_fields_for_merge(
            origin, {"email": "c@x.com", "gender": "f"}, NOW, 365
        )
        missing = apply_overrides(
            suggestions, move_fields=["email"], keep_fields=["gender", "bogus"]
        )
        by_field = suggestions_by_field(suggestions)
        self.assertEqual(missing, ["bogus"])
        self.assertEqual(by_field["email"].target_value, "c@x.com")
        self.assertEqual(by_field["email"].dest_value, "a@x.com")
        self.assertEqual(by_field["gender"].action, "keep")
        self.assertEqual(by_field["gender"].target_value, "")
        self.assertEqual(by_field["gender"].dest_value, "f")
