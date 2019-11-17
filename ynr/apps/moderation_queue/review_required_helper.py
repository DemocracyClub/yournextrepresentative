import abc
from collections import namedtuple
from enum import Enum, unique

from django.conf import settings


class BaseReviewRequiredDecider(metaclass=abc.ABCMeta):
    """
    A base class that decides if a given LoggedAction needs to be flagged
    as requiring review
    """

    @unique
    class Status(Enum):
        UNDECIDED = None
        NEEDS_REVIEW = 1
        NO_REVIEW_NEEDED = 2

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
        if self.logged_action.user:
            user_edits = self.logged_action.user.loggedaction_set.count()
            if user_edits < settings.NEEDS_REVIEW_FIRST_EDITS:
                return self.Status.NEEDS_REVIEW
        return self.Status.UNDECIDED


class DeadCandidateEditsDecider(BaseReviewRequiredDecider):
    """
    Flag edits to candidates that have died
    """

    def review_description_text(self):
        return "Edit of a candidate who has died"

    def needs_review(self):
        if self.logged_action.person:
            has_death_date = self.logged_action.person.death_date
            if has_death_date:
                return self.Status.NEEDS_REVIEW
        return self.Status.UNDECIDED


class HighProfileCandidateEditDecider(BaseReviewRequiredDecider):
    """
    Flag edits to people who's edit_limitations are `NEEDS_REVIEW`
    """

    def review_description_text(self):
        return "Edit of a candidate whose record may be particularly liable to vandalism"

    def needs_review(self):
        if self.logged_action.person:
            if self.logged_action.person.liable_to_vandalism:
                return self.Status.NEEDS_REVIEW
        return self.Status.UNDECIDED


class CandidateStatementEditDecider(BaseReviewRequiredDecider):
    """
    Flag edits to candidates statements
    """

    def review_description_text(self):
        return "Edit of a statement to voters"

    def needs_review(self):
        if self.logged_action.person:
            la = self.logged_action
            for version_diff in la.person.version_diffs:
                if version_diff["version_id"] == la.popit_person_new_version:
                    this_diff = version_diff["diffs"][0]["parent_diff"]
                    for op in this_diff:
                        if op["path"] == "biography":
                            # this is an edit to a biography / statement
                            return self.Status.NEEDS_REVIEW
        return self.Status.UNDECIDED


class EditMadeByBotDecider(BaseReviewRequiredDecider):
    """
    Marks an edit as not needing review if it was made by a bot
    """

    def review_description_text(self):
        return "Edit made by bot"

    def needs_review(self):
        BOT_USERS = (
            settings.TWITTER_BOT_USERNAME,
            settings.CANDIDATE_BOT_USERNAME,
            settings.RESULTS_BOT_USERNAME,
        )
        if (
            self.logged_action.user
            and self.logged_action.user.username in BOT_USERS
        ):
            return self.Status.NO_REVIEW_NEEDED
        return self.Status.UNDECIDED


class CandidateCurrentNameDecider(BaseReviewRequiredDecider):
    """
    Marks an edit as not needing review if it was made by a bot
    """

    def review_description_text(self):
        return "Edit of name of current candidate"

    def needs_review(self):

        if self.logged_action.user and self.logged_action.person:
            la = self.logged_action
            qs = la.person.memberships.filter(
                ballot__election__current=True, ballot__candidates_locked=True
            )
            if qs.exists():
                # This person is standing in a current election
                for version_diff in la.person.version_diffs:
                    if (
                        version_diff["version_id"]
                        == la.popit_person_new_version
                    ):
                        this_diff = version_diff["diffs"][0]["parent_diff"]
                        for op in this_diff:

                            if op["path"] == "name" and op["op"] == "replace":
                                # this is an edit to a name
                                return self.Status.NEEDS_REVIEW
            return self.Status.UNDECIDED


ReviewType = namedtuple("ReviewType", ["type", "label", "cls"])

REVIEW_TYPES = (
    ReviewType(
        type="no_review_needed_due_to_user_being_a_bot",
        label="Edit made by bot",
        cls=EditMadeByBotDecider,
    ),
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
    ReviewType(
        type="needs_review_due_to_current_candidate_name_change",
        label="Edit of name of current candidate",
        cls=CandidateCurrentNameDecider,
    ),
)
