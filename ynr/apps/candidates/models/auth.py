from django.conf import settings

from auth_helpers.views import user_in_group

TRUSTED_TO_MERGE_GROUP_NAME = "Trusted To Merge"
TRUSTED_TO_LOCK_GROUP_NAME = "Trusted To Lock"
TRUSTED_TO_RENAME_GROUP_NAME = "Trusted To Rename"
RESULT_RECORDERS_GROUP_NAME = "Result Recorders"


class NameChangeDisallowedException(Exception):
    pass


class ChangeToLockedConstituencyDisallowedException(Exception):
    pass


def is_post_locked(post, election):
    return post.ballot_set.filter(
        election=election, candidates_locked=True
    ).exists()


def get_constituency_lock_from_person_data(
    user, api, election, person_popit_data
):
    """Return whether the constituency is locked and whether this user can edit"""

    standing_in = person_popit_data.get("standing_in", {}) or {}
    standing_in_election = standing_in.get(election, {}) or {}
    return get_constituency_lock(user, api, standing_in_election.get("post_id"))


def get_constituency_lock(user, ballot=None, post=None, election=None):
    """
    Return whether the constituency is locked and whether this user can edit
    """
    if not ballot:
        # TODO: remove this when we remove `check_update_allowed`
        ballot = election.ballot_set.get(post=post)

    edits_allowed = ballot.user_can_edit_membership(user)
    return ballot.candidates_locked, edits_allowed


def check_creation_allowed(user, new_candidacies):
    for candidacy in new_candidacies:
        ballot = candidacy.ballot
        dummy, edits_allowed = get_constituency_lock(user, ballot)
        if not edits_allowed:
            raise ChangeToLockedConstituencyDisallowedException(
                "The candidates for this ballot are locked now"
            )
