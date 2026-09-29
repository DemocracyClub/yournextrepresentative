from datetime import datetime

from django.test import SimpleTestCase
from splitting.provenance import (
    COMPARABLE_FIELDS,
    changed_fields,
    find_origin,
    flatten,
    last_set_at,
    versions_belonging_to,
)

BALLOT = "local.foo.bar.2024-05-02"
OTHER_BALLOT = "parl.dulwich.2019-12-12"


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
