from django.conf import settings


def needs_review_due_to_statement_edit(logged_action_qs):
    las_with_statements_changed = []
    for la in logged_action_qs:
        if not la.person:
            continue
        for version_diff in la.person.version_diffs:
            if version_diff["version_id"] == la.popit_person_new_version:
                this_diff = version_diff["diffs"][0]["parent_diff"]
                for op in this_diff:
                    if op["path"] == "biography":
                        # this is an edit to a biography / statement
                        las_with_statements_changed.append(la)

    return {
        la: ["Edit of a statement to voters"]
        for la in las_with_statements_changed
    }


needs_review_fns = [
    # needs_review_due_to_statement_edit,
]
