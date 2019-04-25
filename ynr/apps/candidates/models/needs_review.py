from django.conf import settings
from django.contrib.auth.models import User
from django.core.cache import cache
from django.utils.translation import ugettext as _

# This is the number of the first edits of a user that are considered
# to need review.
NEEDS_REVIEW_FIRST_EDITS = 3


# These functions are a bit annoying to write, because
# logged_action_qs is typically the result of a slice, and you're not
# allowed to do chain filter() or various other methods after slicing
# a queryset.


def needs_review_due_to_first_edits(logged_action_qs):
    from candidates.models import LoggedAction

    user_ids = set(logged_action_qs.values_list("user", flat=True))
    # Find the first three edits of each of these users. I can't see a
    # simple way of making this efficient query-wise, so let's cache
    # them.
    user_id_to_user = {u.id: u for u in User.objects.filter(pk__in=user_ids)}
    needs_review_la_ids = set()
    for user_id in user_ids:
        cache_key = "earliest_edits_for_user_id:{}".format(user_id)
        earliest_edits = cache.get(cache_key)
        if (
            earliest_edits is None
            or len(earliest_edits) < NEEDS_REVIEW_FIRST_EDITS
        ):
            earliest_edits = (
                LoggedAction.objects.filter(user_id=user_id)
                .order_by("created")[:NEEDS_REVIEW_FIRST_EDITS]
                .values_list("pk", flat=True)
            )
            cache.set(cache_key, earliest_edits)
        for la_id in earliest_edits:
            needs_review_la_ids.add(la_id)
    return {
        la: [
            _("One of the first {n} edits of user {username}").format(
                n=NEEDS_REVIEW_FIRST_EDITS,
                username=user_id_to_user[la.user_id].username,
            )
        ]
        for la in logged_action_qs
        if la.id in needs_review_la_ids
    }


def needs_review_due_to_subject_having_died(logged_action_qs):
    from people.models import Person

    person_ids = logged_action_qs.values_list("person", flat=True)
    person_ids = {p for p in person_ids if p is not None}
    dead_people_ids = set(
        Person.objects.filter(pk__in=person_ids)
        .exclude(death_date="")
        .values_list("pk", flat=True)
    )
    return {
        la: [_("Edit of a candidate who has died")]
        for la in logged_action_qs
        if la.person_id in dead_people_ids
    }


def needs_review_due_to_candidate_specifically(logged_action_qs):
    person_ids = set(logged_action_qs.values_list("person", flat=True))
    needs_review_person_ids = person_ids & settings.PEOPLE_LIABLE_TO_VANDALISM
    return {
        la: [
            _(
                "Edit of a candidate whose record may be particularly liable to vandalism"
            )
        ]
        for la in logged_action_qs
        if la.person_id in needs_review_person_ids
    }


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
        la: [_("Edit of a statement to voters")]
        for la in las_with_statements_changed
    }


needs_review_fns = [
    needs_review_due_to_first_edits,
    needs_review_due_to_subject_having_died,
    needs_review_due_to_candidate_specifically,
    # needs_review_due_to_statement_edit,
]
