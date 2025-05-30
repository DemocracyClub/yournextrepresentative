from collections import defaultdict
from datetime import datetime, timedelta
from enum import Enum, unique

from django.contrib.auth.models import User
from django.contrib.postgres.fields import ArrayField
from django.db import models, transaction
from django.db.models import JSONField
from django.urls import reverse
from django.utils.html import escape
from django.utils.safestring import mark_safe
from django_extensions.db.models import TimeStampedModel
from moderation_queue.review_required_helper import (
    POST_DECISION_REVIEW_TYPES,
    REVIEW_TYPES,
)
from moderation_queue.slack import post_action_to_slack


class LoggedActionQuerySet(models.QuerySet):
    def in_recent_days(self, days=5):
        return self.filter(created__gte=(datetime.now() - timedelta(days=days)))

    def needs_review(self):
        return self.exclude(flagged_type="").order_by("-created")


@unique
class EditType(Enum):
    USER = "User"
    BOT = "Bot"
    BULK_ADD = "Bulk Add"


class ActionType(models.TextChoices):
    ENTERED_RESULTS_DATA = "entered-results-data", "Entered results"
    SET_CANDIDATE_ELECTED = "set-candidate-elected", "Set Candidate elected"
    SET_CANDIDATE_NOT_ELECTED = (
        "set-candidate-not-elected",
        "Set Candidate not elected",
    )
    PERSON_LOCK = "person-lock", "Person locked"
    PERSON_UPDATE = "person-update", "Person updated"
    PERSON_CREATE = "person-create", "Person created"
    PERSON_DELETE = "person-delete", "Person deleted"
    PERSON_OTHER_NAME_CREATE = (
        "person-other-name-create",
        "Person Other name created",
    )
    PERSON_OTHER_NAME_DELETE = (
        "person-other-name-delete",
        "Person Other name deleted",
    )
    PERSON_OTHER_NAME_UPDATE = (
        "person-other-name-update",
        "Person Other name updated",
    )
    PERSON_REVERT = "person-revert", "Person reverted"
    CONSTITUENCY_LOCK = "constituency-lock", "Constituency locked"
    CONSTITUENCY_UNLOCK = "constituency-unlock", "Constituency unlocked"
    CANDIDACY_CREATE = "candidacy-create", "Candidacy created"
    CANDIDACY_DELETE = "candidacy-delete", "Candidacy deleted"
    PHOTO_APPROVE = "photo-approve", "Photo approved"
    PHOTO_UPLOAD = "photo-upload", "Photo uploaded"
    PHOTO_REJECT = "photo-reject", "Photo rejected"
    PHOTO_IGNORE = "photo-ignore", "Photo ignored"
    SUGGEST_BALLOT_LOCK = "suggest-ballot-lock", "Suggested ballot lock"
    PERSON_MERGE = "person-merge", "Person merged"
    RECORD_COUNCIL_RESULT = "record-council-result", "Recorded council result"
    CONFIRM_COUNCIL_RESULT = (
        "confirm-council-result",
        "Confirmed council result ",
    )
    SOPN_UPLOAD = "sopn-upload", "SOPN uploaded"
    SOPN_SPLIT_BALLOTS = "sopn-split", "Split a SOPN in to ballots"
    RECORD_COUNCIL_CONTROL = (
        "record-council-control",
        "Recorded council control",
    )
    CONFIRM_COUNCIL_CONTROL = (
        "confirm-council-control",
        "Confirmed council control",
    )
    RETRACT_WINNER = "retract-winner", "Retracted winner"
    DUPLICATE_SUGGEST = "duplicate-suggest", "Duplicate suggested"
    CHANGE_EDIT_LIMITATIONS = (
        "change-edit-limitations",
        "Changed edit limitations",
    )
    SUSPENDED_TWITTER_ACCOUNT = (
        "suspended-twitter-account",
        "Suspended Twitter account",
    )
    DELETED_PARSED_RAW_PEOPLE = (
        "deleted-parsed-raw-people",
        "Deleted parsed RawPeople",
    )
    BULK_ADD_BY_PARTY = ("bulk-add-by-party", "Bulk add by party")

    def get_action_type_display():
        return ActionType.choices


class LoggedAction(models.Model):
    """A model for logging the actions of users on the site

    We record the changes that have been made to a person in PopIt in
    that person's 'versions' field, but is not much help for queries
    like "what has John Q User been doing on the site?". The
    LoggedAction model makes that kind of query easy, however, and
    should be helpful in tracking down both bugs and the actions of
    malicious users."""

    user = models.ForeignKey(
        User, blank=True, null=True, on_delete=models.CASCADE
    )
    person = models.ForeignKey(
        "people.Person", blank=True, null=True, on_delete=models.SET_NULL
    )
    person_pk = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text="This is stored to help us identify the related person an action was for after the Person has been deleted",
    )
    action_type = models.CharField(max_length=64, choices=ActionType.choices)
    popit_person_new_version = models.CharField(max_length=32)
    created = models.DateTimeField(auto_now_add=True, db_index=True)
    updated = models.DateTimeField(auto_now=True)
    ip_address = models.CharField(max_length=50, blank=True, null=True)
    source = models.TextField()
    post = models.ForeignKey(
        "popolo.Post", blank=True, null=True, on_delete=models.CASCADE
    )
    ballot = models.ForeignKey(
        "candidates.Ballot", null=True, on_delete=models.CASCADE
    )
    election = models.ForeignKey(
        "elections.Election", null=True, on_delete=models.CASCADE
    )

    flagged_type = models.CharField(
        max_length=100,
        blank=True,
        null=False,
        help_text="If NOT NULL, a type of flag that marks "
        "this edit as needing review by a human",
    )
    flagged_reason = models.CharField(
        max_length=255,
        blank=True,
        null=False,
        help_text="An explaination of the reason for flagging this edit",
    )
    edit_type = models.CharField(
        null=False,
        blank=False,
        choices=[(edit_type.name, edit_type.value) for edit_type in EditType],
        default=EditType.USER.name,
        max_length=20,
    )
    version_fields = ArrayField(
        models.CharField(max_length=200),
        null=True,
        blank=True,
        help_text="The fields that have changed",
    )

    approved = JSONField(null=True)

    objects = LoggedActionQuerySet.as_manager()

    def __str__(self):
        username = None
        if self.user:
            username = self.user.username
        return f"username='{username}' action_type='{self.action_type}'"

    @property
    def subject_url(self):
        ballot = self.ballot
        if ballot:
            return ballot.get_absolute_url()
        if self.person:
            return reverse("person-view", kwargs={"person_id": self.person.id})
        return "/"

    @property
    def subject_html(self):
        ballot = self.ballot
        if ballot:
            return '<a href="{url}">{text} ({post_slug})</a>'.format(
                url=self.subject_url,
                text=ballot.post.short_label,
                post_slug=ballot.post.slug,
            )
        if self.person:
            return '<a href="{url}">{text} ({person_id})</a>'.format(
                url=self.subject_url,
                text=self.person.name,
                person_id=self.person.id,
            )
        return ""

    def friendly_description(self):
        url = self.subject_url
        prefix = ""
        desc = ""
        output = f"""{prefix} {self.action_type} TODO"""
        if self.user:
            prefix = f"User <strong>{self.user.username}</strong>"
        if self.ballot:
            desc = (
                f"""updated <a href="{url}">{self.ballot.ballot_paper_id}</a>"""
            )
            if self.action_type == ActionType.CONSTITUENCY_LOCK:
                desc = f"""locked <a href="{url}">{self.ballot.ballot_paper_id}</a>"""
            if self.action_type == ActionType.CONSTITUENCY_UNLOCK:
                desc = f"""unlocked <a href="{url}">{self.ballot.ballot_paper_id}</a>"""
            if self.action_type == ActionType.ENTERED_RESULTS_DATA:
                desc = f"""entered results data for <a href="{url}">{self.ballot.ballot_paper_id}</a>"""
            if self.action_type == ActionType.SUGGEST_BALLOT_LOCK:
                desc = f"""suggested locking ballot <a href="{url}">{self.ballot.ballot_paper_id}</a>"""
            if self.action_type == ActionType.SOPN_UPLOAD and self.ballot.sopn:
                desc = f"""uploaded <a href="{self.ballot.sopn.get_absolute_url}">a SOPN</a> for <a href="{url}">{self.ballot.ballot_paper_id}</a>"""
        if self.person:
            if self.action_type == ActionType.PERSON_CREATE:
                desc = f"""created <a href="{url}">a new candidate</a>"""
            if self.action_type == ActionType.PERSON_UPDATE:
                desc = f"""updated <a href="{url}">a new candidate</a>"""
            if self.action_type == ActionType.PERSON_DELETE:
                desc = f"""deleted person with ID {self.person_pk}"""
            if self.action_type == ActionType.PERSON_MERGE:
                desc = f"""merged another candidate into <a href="{url}">candidate #{self.person.id}</a>"""
            if self.action_type == ActionType.PHOTO_UPLOAD:
                desc = f"""uploaded a photo of <a href="{url}">candidate #{self.person.id}</a> for moderation"""
            if self.action_type == ActionType.PHOTO_APPROVE:
                desc = f"""approved an uploaded photo of <a href="{url}">candidate #{self.person.id}</a>"""
            if self.action_type == ActionType.PHOTO_REJECT:
                desc = f"""rejected an uploaded photo of <a href="{url}">candidate #{self.person.id}</a>"""
            if self.action_type == ActionType.PERSON_REVERT:
                desc = f"""reverted to an earlier version of <a href="{url}">candidate #{self.person.id}</a>"""
            if self.action_type == ActionType.CANDIDACY_CREATE:
                desc = f"""confirmed candidacy for <a href="{url}">candidate #{self.person.id}</a>"""
            if self.action_type == ActionType.CANDIDACY_DELETE:
                desc = f"""removed candidacy for <a href="{url}">candidate #{self.person.id}</a>"""
            if self.action_type == ActionType.DUPLICATE_SUGGEST:
                desc = f"""Suggested a duplicate of <a href="{url}">{self.person.name}</a>"""
            if self.action_type == ActionType.DUPLICATE_SUGGEST:
                desc = f"""Suggested a duplicate of <a href="{url}">{self.person.name}</a>"""
            if self.action_type == ActionType.SET_CANDIDATE_ELECTED:
                desc = f"""marked <a href="{url}">candidate #{self.person.id}</a> as elected"""
            if self.action_type == ActionType.PERSON_OTHER_NAME_CREATE:
                desc = f"""added an alternate name for <a href="{url}">candidate #{self.person.id}</a>"""
            if self.action_type == ActionType.PERSON_OTHER_NAME_DELETE:
                desc = f"""removed an alternate name for <a href="{url}">candidate #{self.person.id}</a>"""
            if self.action_type == ActionType.PERSON_OTHER_NAME_UPDATE:
                desc = f"""changed an alternate name for <a href="{url}">candidate #{self.person.id}</a>"""
            if self.action_type == ActionType.SUSPENDED_TWITTER_ACCOUNT:
                desc = f"""updated twitter account status for <a href="{url}">candidate #{self.person.id}</a>"""
            if self.action_type == ActionType.ENTERED_RESULTS_DATA:
                desc = f"""entered results data for <a href="{url}">{self.person.name}</a>"""

        if desc:
            output = f"{prefix} {desc}"
        return mark_safe(output)

    @property
    def diff_html(self):
        from popolo.models import VersionNotFound

        if not self.person:
            return ""
        try:
            return self.person.diff_for_version(
                self.popit_person_new_version, inline_style=True
            )
        except VersionNotFound as e:
            return "<p>{}</p>".format(escape(str(e)))

    def changed_version_fields(self):
        if not self.version_fields:
            return ""
        pretty_fieldnames = [
            field.replace("_", " ").title() for field in self.version_fields
        ]
        return ", ".join(pretty_fieldnames)

    def candidacy_edit(self):
        if self.version_fields and "candidacies" in self.diff_html:
            return True
        return None

    def set_review_required(self):
        """
        Runs all `ReviewRequiredDecider` classed over a LoggedAction
        and sets the flags accordingly

        """
        for review_stage in [REVIEW_TYPES, POST_DECISION_REVIEW_TYPES]:
            for review_type in review_stage:
                decider = review_type.cls(self)
                decision = decider.needs_review()
                if decision == review_type.cls.Status.NEEDS_REVIEW:
                    self.flagged_type = review_type.type
                    self.flagged_reason = decider.review_description_text()
                    break
                if decision == review_type.cls.Status.NO_REVIEW_NEEDED:
                    self.flagged_type = ""
                    self.flagged_reason = ""
                    break

    def save(self, **kwargs):
        has_initial_pk = self.pk
        if not kwargs.get("review_not_required", False):
            self.set_review_required()

        if self.person:
            version_id = self.popit_person_new_version
            self.person_pk = self.person.pk
            self.version_fields = self.person.version_fields(version_id)
        super().save(**kwargs)

        if (
            not has_initial_pk
            and self.flagged_type
            and self.person
            and self.edit_type == "USER"
        ):
            transaction.on_commit(post_action_to_slack.s(self.pk).delay)


class PersonRedirect(TimeStampedModel):
    """This represents a redirection from one person ID to another

    This is typically used to redirect from the person that is deleted
    after two people are merged"""

    old_person_id = models.IntegerField()
    new_person_id = models.IntegerField()

    @classmethod
    def all_redirects_dict(cls):
        new_to_sorted_old = defaultdict(list)
        for old, new in cls.objects.values_list(
            "old_person_id", "new_person_id"
        ):
            new_to_sorted_old[new].append(old)
            new_to_sorted_old[new].sort()
        return new_to_sorted_old
