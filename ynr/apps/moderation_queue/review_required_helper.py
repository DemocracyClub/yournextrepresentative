import abc
from collections import namedtuple

from django.conf import settings


class BaseReviewRequiredDecider(metaclass=abc.ABCMeta):
    """
    A base class that decides if a given LoggedAction needs to be flagged
    as requiring review
    """

    def __init__(self, logged_action):
        """
        :type logged_action: candidates.models.LoggedAction
        """
        self.logged_action = logged_action

    @abc.abstractmethod
    def review_description_text(self):
        """
        Returns an explanation of why the edit is being marked as requiring a
        review
        """

    @abc.abstractmethod
    def needs_review(self):
        """
        Takes a LoggedAction model and returns True if that action if judged to
        need review by a human for some reason.

        """
        return False


class FirstByUserEditsDecider(BaseReviewRequiredDecider):
    """
    An edit needs review if its one of the first edits by that user,
    as defined by settings.NEEDS_REVIEW_FIRST_EDITS

    """

    def review_description_text(self):
        return "One of the first {n} edits of user {username}".format(
            username=self.logged_action.user.username,
            n=settings.NEEDS_REVIEW_FIRST_EDITS,
        )

    def needs_review(self):
        if not self.logged_action.user:
            return False
        user_edits = self.logged_action.user.loggedaction_set.count()
        return user_edits < settings.NEEDS_REVIEW_FIRST_EDITS


class DeadCandidateEditsDecider(BaseReviewRequiredDecider):
    """
    Flag edits to candidates that have died
    """

    def review_description_text(self):
        return "Edit of a candidate who has died"

    def needs_review(self):
        if not self.logged_action.person:
            return False
        has_death_date = self.logged_action.person.death_date
        return bool(has_death_date)


class HighProfileCandidateEditDecider(BaseReviewRequiredDecider):
    """
    Flag edits to candidates on the PEOPLE_LIABLE_TO_VANDALISM list
    """

    def review_description_text(self):
        return "Edit of a candidate whose record may be particularly liable to vandalism"

    def needs_review(self):
        if not self.logged_action.person:
            return False
        return (
            int(self.logged_action.person.pk)
            in settings.PEOPLE_LIABLE_TO_VANDALISM
        )


class CandidateStatementEditDecider(BaseReviewRequiredDecider):
    """
    Flag edits to candidates statements
    """

    def review_description_text(self):
        return "Edit of a statement to voters"

    def needs_review(self):
        if not self.logged_action.person:
            return False

        la = self.logged_action
        for version_diff in la.person.version_diffs:
            if version_diff["version_id"] == la.popit_person_new_version:
                this_diff = version_diff["diffs"][0]["parent_diff"]
                for op in this_diff:
                    if op["path"] == "biography":
                        # this is an edit to a biography / statement
                        return True
        return False


ReviewType = namedtuple("ReviewType", ["type", "label", "cls"])

REVIEW_TYPES = (
    ReviewType(
        type="needs_review_due_to_high_profile",
        label="Edit of a candidate whose record may be particularly liable to vandalism",
        cls=HighProfileCandidateEditDecider,
    ),
    ReviewType(
        type="needs_review_due_to_candidate_having_died",
        label="Edit of a candidate who has died",
        cls=DeadCandidateEditsDecider,
    ),
    ReviewType(
        type="needs_review_due_to_first_edits",
        label="First edits by user",
        cls=FirstByUserEditsDecider,
    ),
    ReviewType(
        type="needs_review_due_to_statement_edit",
        label="Edit of a statement to voters",
        cls=CandidateStatementEditDecider,
    ),
)


def set_review_required(logged_action):
    """
    Runs all `ReviewRequiredDecider` classed over a LoggedAction
    and sets the flags on that model accordingly

    :type logged_action: candidates.models.LoggedAction
    """

    for review_type in REVIEW_TYPES:
        decider = review_type.cls(logged_action)
        if decider.needs_review():
            logged_action.flagged_type = review_type.type
            logged_action.flagged_reason = decider.review_description_text()
            break
